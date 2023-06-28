from __future__ import annotations
import discord
from discord.ext import commands

from main import config

from enum import Enum
import time
import json
import os

from utils import (
    text_admin_only,
    Config,
    Color,
)

from typing import TYPE_CHECKING
if TYPE_CHECKING:
    from bot import Bot

    from typing import (
        NotRequired,
        TypedDict,
        Literal,
        Self,
    )

    class _Question(TypedDict):
        title: str
        type: Literal['multiple_choice', 'text_short', 'text_long', 'yes_no']
        # type `multiple_choice`, `text_short` and `text_long` REQUIRE this
        short: NotRequired[str]
        choices: NotRequired[list[str]]  # type `multiple_choice` REQUIRES this
        # type `text_short` and `text_long` REQUIRE this
        max_length: NotRequired[int]
        # type `text_short` and `text_long` REQUIRE this
        placeholder: NotRequired[str]

    class _QuestionShort(TypedDict):
        title: str
        answer: str
        type: Literal['multiple_choice', 'text_short', 'text_long', 'yes_no']
        choices: NotRequired[list[str]]

    class _Answer(TypedDict):
        id: str
        user_id: int
        epoch: int
        questions: list[_QuestionShort]

    class _TagLogic(TypedDict):
        contains: str
        tag_id: int
        case_sensitive: bool


GUILD_ID = config['guild_id']
LOG_CHANNEL_ID = config['log_channel_id']
FORUM_CHANNEL_ID = config['forum_channel_id']
with open('config/questions.json', 'r', encoding='utf-8') as file:
    QUESTIONS: list[_Question] = json.load(file)
with open('config/button_message.txt', 'r') as f:
    BUTTON_MESSAGE = f.read()
with open('config/tag_logic.json', 'r', encoding='utf-8') as file:
    TAG_LOGIC: list[_TagLogic] = json.load(file)


class RejectionMessage(discord.ui.Modal):
    def __init__(
        self,
        bot: Bot,
        cog: 'Cog',
        answer: _Answer,
    ) -> None:
        self.bot: Bot = bot
        self.cog: Cog = cog
        self.answer: _Answer = answer
        super().__init__(timeout=300.0, title='Rejection Message')

        self.message = discord.ui.TextInput(
            label='Message',
            placeholder='Enter a rejection message',
            max_length=2000,
            required=True,
        )
        self.add_item(self.message)

    async def on_submit(self, interaction: discord.Interaction[Bot]) -> None:
        await self.cog.reject_answer(interaction=interaction, answer=self.answer, message=self.message.value)


class AnswerModal(discord.ui.Modal):
    def __init__(
        self,
        bot: Bot,
        cog: 'Cog',
        interaction: discord.Interaction[Bot],
        view: 'QuestionnaireView | LogView',
        question: _Question,
        default: str = '',
    ) -> None:
        self.bot: Bot = bot
        self.cog: Cog = cog
        self.view: 'QuestionnaireView | LogView' = view
        self.interaction: discord.Interaction[Bot] = interaction
        self.question: _Question = question
        super().__init__(timeout=300.0, title=self.question['title'])

        self.answer = discord.ui.TextInput(
            label=self.question['short'],  # type: ignore
            # type: ignore
            style=discord.TextStyle.short if self.question[
                'type'] == 'text_short' else discord.TextStyle.long,
            placeholder=self.question['placeholder'],  # type: ignore
            max_length=self.question['max_length'],  # type: ignore
            default=default,
            required=True,
        )
        self.add_item(self.answer)

    async def on_submit(self, interaction: discord.Interaction[Bot]) -> None:
        await self.view.answer_question(self.answer.value)
        await self.view.update(interaction=interaction)


class AnswerResult(Enum):
    pending = 0
    approved = 1
    rejected = 2


class LogView(discord.ui.View):
    def __init__(
        self,
        bot: Bot,
        cog: 'Cog',
        answer: _Answer,
        result: AnswerResult = AnswerResult.pending,
        question_index: int = -1,  # -1 = not editing
        reject_message: str = '',
    ) -> None:
        super().__init__(timeout=0.01)
        self.bot: Bot = bot
        self.cog: Cog = cog
        self.answer: _Answer = answer
        self.result: AnswerResult = result
        self.question_index: int = question_index
        self.reject_message: str = reject_message

    @property
    def editing(self) -> bool:
        return self.question_index != -1

    @property
    def question(self) -> _QuestionShort:
        if not self.editing:
            raise
        return self.answer['questions'][self.question_index]

    async def answer_question(self, answer: str) -> None:
        self.question['answer'] = answer
        await self.cog.answers.put(self.answer['id'], self.answer)

    def update_components(self) -> None:
        self.clear_items()
        if self.result != AnswerResult.pending:
            if self.result == AnswerResult.approved:
                self.add_item(discord.ui.Button(
                    style=discord.ButtonStyle.green, label='Approved', disabled=True))
            elif self.result == AnswerResult.rejected:
                self.add_item(discord.ui.Button(
                    style=discord.ButtonStyle.red, label='Rejected', disabled=True))
            return

        components: list[discord.ui.Button[Self] | discord.ui.Select[Self]] = [
            discord.ui.Button(style=discord.ButtonStyle.green, label='Approve',
                              custom_id=f'questions:::approve-{self.answer["id"]}', row=0, disabled=self.editing),
            discord.ui.Button(style=discord.ButtonStyle.red, label='Reject',
                              custom_id=f'questions:::reject-{self.answer["id"]}', row=0, disabled=self.editing),
            discord.ui.Button(style=discord.ButtonStyle.blurple, label='Edit' if not self.editing else 'Stop Editing',
                              custom_id=f'questions:::edit-{self.answer["id"]}-{1 if self.editing else 0}', row=0),
        ]

        if self.editing:
            components.extend([
                discord.ui.Button(style=discord.ButtonStyle.grey, label=' ', emoji='⬆️',
                                  custom_id=f'questions:::index_up-{self.answer["id"]}-{self.question_index}', row=0),
                discord.ui.Button(style=discord.ButtonStyle.grey, label=' ', emoji='⬇️',
                                  custom_id=f'questions:::index_down-{self.answer["id"]}-{self.question_index}', row=0),
            ])

            if self.question['type'] == 'multiple_choice':
                components.append(discord.ui.Select(
                    placeholder=f'{self.question["title"]} [CLICK]',
                    options=[
                        discord.SelectOption(
                            label=choice, value=choice, default=choice == self.question['answer'])
                        for choice in self.question['choices']  # type: ignore
                    ],
                    custom_id=f'questions:::multiple_choice-{self.answer["id"]}-{self.question_index}',
                    row=1,
                ))
            elif self.question['type'] in ('text_short', 'text_long'):
                components.append(discord.ui.Button(
                    label='Edit Question Answer',
                    style=discord.ButtonStyle.red,
                    custom_id=f'questions:::text-{self.answer["id"]}-{self.question_index}',
                    row=1,
                ))
            elif self.question['type'] == 'yes_no':
                components.append(discord.ui.Button(
                    label='Yes',
                    style=discord.ButtonStyle.green,
                    custom_id=f'questions:::yes-{self.answer["id"]}-{self.question_index}',
                    row=1,
                    disabled=self.question['answer'].lower() == 'yes',
                ))
                components.append(discord.ui.Button(
                    label='No',
                    style=discord.ButtonStyle.red,
                    custom_id=f'questions:::no-{self.answer["id"]}-{self.question_index}',
                    row=1,
                    disabled=self.question['answer'].lower() == 'no',
                ))

        for component in components:
            self.add_item(component)

    @property
    def embed(self) -> discord.Embed:
        embed = self.bot.embed(title='Questionnaire Answer')
        embed.description = f'**Answered By:** <@{self.answer["user_id"]}>\n**Questions:**'
        for i, question in enumerate(self.answer['questions'], start=1):
            embed.add_field(
                name=('👉 ' if self.editing and (i == self.question_index+1)
                      else '') + f'**#{i}. {question["title"]}**',
                value=f'> {question["answer"]}',
                inline=False,
            )
        if self.reject_message:
            embed.add_field(name='**Rejected:**',
                            value=f'{self.reject_message}', inline=False)
        return embed

    async def run(self) -> None:
        self.update_components()
        await self.cog.log_channel.send(embed=self.embed, view=self)

    async def update(self, interaction: discord.Interaction) -> None:
        await self.edit(interaction=interaction)

    async def edit(self, interaction: discord.Interaction) -> None:
        self.update_components()
        await interaction.response.edit_message(embed=self.embed, view=self)


class QuestionnaireView(discord.ui.View):
    message: discord.Message

    def __init__(
        self,
        bot: Bot,
        cog: 'Cog',
        interaction: discord.Interaction[Bot],
    ) -> None:
        super().__init__(timeout=300.0)
        self.bot: Bot = bot
        self.cog: Cog = cog
        self.interaction: discord.Interaction[Bot] = interaction
        self.answers: list[str] = []
        self.started: bool = False
        # self.recently_answered: bool = False

    @property
    def embed(self) -> discord.Embed:
        embed = self.bot.embed(title='Questionnaire')
        if not self.done:
            embed.description = (
                'Please answer the following questions with the components below.'
                f'\nYou have already answered `{self.answered}/{len(QUESTIONS)}` questions.'
            )
            if self.started:  # and not self.recently_answered:
                embed.add_field(
                    name=f'**Question #{self.answered + 1}**',
                    value=self.question['title'],
                    inline=False,
                )
            # elif self.recently_answered:
            #     embed.add_field(
            #         name=f'**Success!**',
            #         value='Your answer has been recorded.',
            #         inline=False,
            #     )
            else:
                embed.add_field(
                    name='**Start Questionnaire**',
                    value='Click the button below to start the questionnaire.',
                    inline=False,
                )
        else:
            embed.description = 'Thank you for answering all the questions!'
        return embed

    @property
    def question(self) -> _Question:
        return QUESTIONS[len(self.answers)]

    @property
    def answered(self) -> int:
        return len(self.answers)

    @property
    def done(self) -> bool:
        return self.answered == len(QUESTIONS)

    def update_components(self) -> None:
        self.clear_items()
        if self.done:
            return

        components: list[discord.ui.Button[Self]
                         | discord.ui.Select[Self]] = []

        if not self.started:
            components.append(discord.ui.Button(
                label='Start Questionnaire',
                style=discord.ButtonStyle.blurple,
                custom_id='start',
            ))
        # elif self.recently_answered:
        #     components.append(discord.ui.Button(
        #         label='Next Question',
        #         style=discord.ButtonStyle.blurple,
        #         custom_id='next',
        #     ))
        elif self.question['type'] == 'multiple_choice':
            components.append(discord.ui.Select(
                placeholder=f'{self.question["title"]} [CLICK]',
                options=[
                    discord.SelectOption(label=choice, value=choice)
                    for choice in self.question['choices']  # type: ignore
                ],
                custom_id='multiple_choice',
            ))
        elif self.question['type'] in ('text_short', 'text_long'):
            components.append(discord.ui.Button(
                label='Answer Question',
                style=discord.ButtonStyle.red,
                custom_id='text',
            ))
        elif self.question['type'] == 'yes_no':
            components.append(discord.ui.Select(
                placeholder=self.question['title'],
                options=[discord.SelectOption(label='-', value='-')],
                disabled=True,
                row=0,
            ))
            components.append(discord.ui.Button(
                label='Yes',
                style=discord.ButtonStyle.green,
                custom_id='yes',
                row=1,
            ))
            components.append(discord.ui.Button(
                label='No',
                style=discord.ButtonStyle.red,
                custom_id='no',
                row=1,
            ))

        for component in components:
            component.callback = self.callback
            self.add_item(component)

    async def submit(self) -> None:
        id: str = os.urandom(4).hex()
        answer: _Answer = {
            'id': id,
            'user_id': self.interaction.user.id,
            'epoch': int(time.time()),
            'questions': [  # type: ignore
                {
                    'title': question['title'],
                    'type': question['type'],
                    # type: ignore
                    **({'choices': question['choices']} if question['type'] == 'multiple_choice' else {}),
                    **({
                        'short': question['short'],  # type: ignore
                        'placeholder': question['placeholder'],  # type: ignore
                        'max_length': question['max_length'],  # type: ignore
                    } if question['type'] in ('text_short', 'text_long') else {}),  # type: ignore
                    'answer': answer,
                } for question, answer in zip(QUESTIONS, self.answers)
            ]
        }
        await self.cog.answers.put(id, answer)
        view = LogView(bot=self.bot, cog=self.cog, answer=answer)
        await view.run()

    async def update(self, interaction: discord.Interaction[Bot]) -> None:
        self.update_components()
        await interaction.response.edit_message(embed=self.embed, view=self)

        if self.done:
            await self.submit()

    async def answer_question(self, answer: str) -> None:
        self.answers.append(answer)
        # self.recently_answered = True

    async def callback(self, interaction: discord.Interaction[Bot]) -> None:
        custom_id: str = interaction.data['custom_id']  # type: ignore

        if custom_id == 'start':
            self.started = True
        # elif custom_id == 'next':
        #     self.recently_answered = False
        elif custom_id == 'multiple_choice':
            # type: ignore
            await self.answer_question(interaction.data['values'][0])
        elif custom_id == 'text':
            await interaction.response.send_modal(AnswerModal(
                bot=self.bot,
                cog=self.cog,
                interaction=interaction,
                view=self,
                question=self.question,
            ))
            return
        elif custom_id in ('yes', 'no'):
            await self.answer_question(custom_id.capitalize())

        await self.update(interaction=interaction)

    async def run(self) -> None:
        self.update_components()
        await self.interaction.response.send_message(embed=self.embed, view=self, ephemeral=True)
        self.message = await self.interaction.original_response()

    async def on_timeout(self) -> None:
        view = discord.ui.View(timeout=0.01)
        view.add_item(discord.ui.Button(label='Message timed out',
                      style=discord.ButtonStyle.grey, disabled=True))
        await self.message.edit(view=view)


class Cog(commands.Cog):
    def __init__(self, bot: Bot) -> None:
        self.bot: Bot = bot
        self.answers: Config[_Answer] = Config('answers.json')

    @property
    def guild(self) -> discord.Guild:
        return self.bot.get_guild(GUILD_ID)  # type: ignore

    @property
    def log_channel(self) -> discord.TextChannel:
        return self.guild.get_channel(LOG_CHANNEL_ID)  # type: ignore

    @property
    def forum_channel(self) -> discord.ForumChannel:
        return self.guild.get_channel(FORUM_CHANNEL_ID)  # type: ignore

    @commands.command(name='sendbutton')
    @text_admin_only()
    async def send_button(self, ctx: commands.Context) -> None:
        view = discord.ui.View(timeout=0.01)
        view.add_item(discord.ui.Button(
            label='Click me!', style=discord.ButtonStyle.blurple, custom_id='questions:::start'))
        embed = self.bot.embed(BUTTON_MESSAGE)
        await ctx.send(embed=embed, view=view)

    # Prints out a list of all tags for the configured forum.
    # Use these to set up the tag logic
    @commands.command(name='forumtags')
    @text_admin_only()
    async def forum_tags(self, ctx: commands.Context) -> None:
        embed = self.bot.embed(
            title='Forum Tags',
            description='\n'.join(
                f'{(str(tag.emoji) + " ") if tag.emoji else ""}**{tag.name}** (ID: {tag.id})' for tag in self.forum_channel.available_tags) or 'No tags found.',
        )
        await ctx.send(embed=embed)

    async def start_questionnaire(self, interaction: discord.Interaction[Bot]) -> None:
        view = QuestionnaireView(
            bot=self.bot, cog=self, interaction=interaction)
        await view.run()

    def get_tags(self, answer: _Answer) -> list[discord.ForumTag]:
        answers: list[str] = [question['answer']
                              for question in answer['questions']]
        answers_lowered: list[str] = [answer.lower() for answer in answers]

        tag_ids: set[int] = set()
        for logic in TAG_LOGIC:
            contains = logic['contains'] if logic['case_sensitive'] else logic['contains'].lower(
            )
            if any(contains in answer for answer in (
                answers if logic['case_sensitive'] else answers_lowered
            )):
                tag_ids.add(logic['tag_id'])

        tags: list[discord.ForumTag] = [
            self.forum_channel.get_tag(tag_id) for tag_id in tag_ids
        ]  # type: ignore
        return tags

    async def approve_answer(self, interaction: discord.Interaction[Bot], answer: _Answer) -> None:
        await self.answers.remove(answer['id'])

        user: str = str(self.guild.get_member(
            answer['user_id']) or 'Unknown User')
        embed = self.bot.embed(title=f'{user}\'s answers')
        for i, question in enumerate(answer['questions'], start=1):
            embed.add_field(
                name=f'**#{i}: {question["title"]}**',
                value=question['answer'],
                inline=False,
            )
        await self.forum_channel.create_thread(
            # TODO -- Series › Track › IRR#
            name=f'{user}\'s answers',
            embed=embed,
            applied_tags=self.get_tags(answer=answer),
        )

        view = LogView(bot=self.bot, cog=self, answer=answer,
                       result=AnswerResult.approved)
        return await view.edit(interaction=interaction)

    async def reject_message_modal(self, interaction: discord.Interaction[Bot], answer: _Answer) -> None:
        return await interaction.response.send_modal(RejectionMessage(bot=self.bot, cog=self, answer=answer))

    async def reject_answer(self, interaction: discord.Interaction[Bot], answer: _Answer, message: str) -> None:
        await self.answers.remove(answer['id'])
        view = LogView(bot=self.bot, cog=self, answer=answer,
                       result=AnswerResult.rejected, reject_message=message)
        await view.edit(interaction=interaction)

        member = self.guild.get_member(answer['user_id'])
        if member is None:
            return
        embed = self.bot.embed(
            description=f'Your answers have unfortunately been rejected from being posted in {self.forum_channel.mention}.',
        )
        embed.add_field(name='Reason', value=message, inline=False)
        try:
            await member.send(embed=embed)
        except Exception:
            pass

    async def edit_answer(self, interaction: discord.Interaction[Bot], answer: _Answer, already_editing: bool) -> None:
        if already_editing:
            view = LogView(bot=self.bot, cog=self,
                           answer=answer, question_index=-1)
            return await view.edit(interaction=interaction)
        view = LogView(bot=self.bot, cog=self, answer=answer, question_index=0)
        return await view.edit(interaction=interaction)

    async def set_index(self, interaction: discord.Interaction[Bot], answer: _Answer, index: int) -> None:
        view = LogView(bot=self.bot, cog=self,
                       answer=answer, question_index=index)
        return await view.edit(interaction=interaction)

    async def edited_answer(self, interaction: discord.Interaction[Bot], answer: _Answer, question_index: int, new_answer: str) -> None:
        view = LogView(bot=self.bot, cog=self, answer=answer,
                       question_index=question_index)
        await view.answer_question(answer=new_answer)
        return await view.edit(interaction=interaction)

    async def edit_free_text(self, interaction: discord.Interaction[Bot], answer: _Answer, question_index: int) -> None:
        view = LogView(bot=self.bot, cog=self, answer=answer,
                       question_index=question_index)
        question: _QuestionShort = answer['questions'][question_index]
        modal = AnswerModal(
            bot=self.bot,
            cog=self,
            interaction=interaction,
            view=view,
            question=question,  # type: ignore
            default=question['answer'],
        )
        return await interaction.response.send_modal(modal)

    async def on_button_click(
        self,
        interaction: discord.Interaction[Bot],
        keyword: str,
    ) -> None:
        try:
            base, rest = keyword.split('-', 1)
        except ValueError:
            base, rest = keyword, ''

        if base == 'start':
            return await self.start_questionnaire(interaction=interaction)

        try:
            id, rest_no_id = rest.split('-', 1)
        except ValueError:
            id, rest_no_id = rest, ''

        answer = self.answers.get(id)
        if answer is None:
            return await interaction.response.send_message(embed=self.bot.embed('I could not seem to find this asnwer..', color=Color.error), ephemeral=True)

        if base == 'approve':
            return await self.approve_answer(interaction=interaction, answer=answer)
        elif base == 'reject':
            return await self.reject_message_modal(interaction=interaction, answer=answer)
        elif base == 'edit':
            return await self.edit_answer(interaction=interaction, answer=answer, already_editing=rest_no_id == '1')
        elif base in ('index_up', 'index_down'):
            index: int = (int(rest_no_id) + (-1 if base ==
                          'index_up' else 1)) % len(answer['questions'])
            return await self.set_index(interaction=interaction, answer=answer, index=index)
        elif base in ('multiple_choice', 'yes', 'no'):
            new_answer: str = base.capitalize() if base in (
                'yes', 'no') else interaction.data['values'][0]  # type: ignore
            return await self.edited_answer(interaction=interaction, answer=answer, question_index=int(rest_no_id), new_answer=new_answer)
        elif base == 'text':
            return await self.edit_free_text(interaction=interaction, answer=answer, question_index=int(rest_no_id))
        else:
            raise  # should not happen

    @commands.Cog.listener()
    async def on_interaction(self, interaction: discord.Interaction[Bot]) -> None:
        if interaction.type != discord.InteractionType.component:
            return
        custom_id: str = interaction.data['custom_id']  # type: ignore
        try:
            prefix, keyword = custom_id.split(':::', 1)
        except ValueError:
            return
        if prefix != 'questions':
            return

        # type: ignore
        await self.on_button_click(interaction=interaction, keyword=keyword)


async def setup(bot: Bot) -> None:
    await bot.add_cog(Cog(bot))
