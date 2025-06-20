import os
from datetime import datetime, timedelta
from math import ceil
from time import mktime

import discord
from discord import app_commands
from discord.ext import commands

from custom_logger import Logger

logger = Logger('gwaff.bot.stats')

from predictor import Prediction, xp_to_lvl
from predictor import (NoDataError, ZeroGrowthError,
                       TargetBoundsError)
from truerank import Truerank
from utils import resolve_member, ordinal

GRAPH_MAX_DAYS: int = int(os.environ.get("GRAPH_MAX_DAYS", 365))
PREDICTOR_DEFAULT_DAYS: int = int(os.environ.get("PREDICTOR_DEFAULT_DAYS", 30))
RANK_DEFAULT_THRESHOLD: int = int(os.environ.get("RANK_DEFAULT_THRESHOLD", 30))
RANK_MAX_PAGE: int = 5
RANK_PAGE_SIZE: int = 25
ACCENT_COLOUR: str = '#ea625e'


class StatsCog(commands.Cog):
    def __init__(self, bot: commands.Bot):
        self.bot = bot

        self.truerank_ctxmenu = app_commands.ContextMenu(
            name='True Rank',
            callback=self.truerank_ctx
        )
        self.bot.tree.add_command(self.truerank_ctxmenu)

    @app_commands.command(name="predict",
                          description="Predict when you will pass a given level, "
                                      "xp, or member")
    @app_commands.describe(target='Either a level, xp, or member to aim for',
                           member='The member to do the prediction for'
                                  ' (default you)',
                           period='The period to average your growth over'
                                  ' (default 30 days)',
                           growth='Override the average daily growth calculation',
                           hidden='Hide from others in this server (default False)')
    async def predict(self, interaction: discord.Interaction,
                      target: str,
                      member: discord.User = None,
                      period: app_commands.Range[
                          int, 1, GRAPH_MAX_DAYS] = PREDICTOR_DEFAULT_DAYS,
                      growth: int = None,
                      hidden: bool = False):
        await interaction.response.defer(ephemeral=hidden)

        member = resolve_member(interaction, member)
        if member is False:
            await interaction.followup.send(":bust_in_silhouette: "
                                            "That person in not in the server "
                                            "or hasn't reached level 15")
            return
        elif target == member:
            await interaction.followup.send(":mirror: "
                                            "The target cannot be the same as "
                                            "the member")
            return

        try:
            prediction = Prediction(member=member.id,
                                    target=target,
                                    period=period,
                                    growth=growth)
            days = prediction.evaluate()

        except ValueError:
            await interaction.followup.send(":1234: "
                                            "Level or xp must be a whole number")
            return
        except ZeroGrowthError:
            await interaction.followup.send(":chart_with_downwards_trend: "
                                            "That person has earnt no xp recently")
            return
        except NoDataError:
            await interaction.followup.send(":mag: That target does not exist")
            return
        except TargetBoundsError:
            await interaction.followup.send(":telescope: "
                                            "That target is too far away")
            return
        except Exception as e:
            await interaction.followup.send(f":question: An unknown error occurred:\n {e}")
            raise e

        date = mktime((datetime.now() + timedelta(days=days)).timetuple())
        member_name = "You" if member is interaction.user else f"<@{member.id}>"

        target: str
        if prediction.target_type == 'xp':
            target = str(int(prediction.target)) + ' xp'
        elif prediction.target_type == 'level':
            target = 'level ' + str(prediction.target)
        elif prediction.target_type == 'user':
            target = str(target)
            if not target.startswith("<@"):
                target = f"<@{target}>"
            if days <= 0:
                await interaction.followup.send(f"{member_name} will never reach "
                                                f"{target} at this rate")
                return
        else:
            target = str(target)

        await interaction.followup.send(f"{member_name} will reach {target} on "
                                        f"<t:{round(date)}:D> <t:{round(date)}:R> "
                                        f"at a rate of {round(prediction.growth)} "
                                        f"xp per day")

    @app_commands.command(name="truerank",
                          description="Tells you your position out of only active members")
    @app_commands.describe(member='The member to check (default you)',
                           threshold=f"The monthly xp needed to be listed "
                                     f"(default {RANK_DEFAULT_THRESHOLD})",
                           hidden='Hide from others in this server (default False)')
    async def rank_true(self, interaction: discord.Interaction,
                        member: discord.User = None,
                        threshold: int = RANK_DEFAULT_THRESHOLD,
                        hidden: bool = False):
        await interaction.response.defer(ephemeral=hidden)

        member = resolve_member(interaction, member)
        if member is False:
            await interaction.followup.send(":bust_in_silhouette: "
                                            "That person in not in the server "
                                            "or hasn't reached level 15")
            return
        try:
            truerank = Truerank(threshold=threshold)
            result = truerank.find_index(member.id)
        except IndexError:
            await interaction.followup.send(":bust_in_silhouette: "
                                            "That person has not been online "
                                            "recently enough")
            return

        member_name = "You are" if member == interaction.user \
            else f"<@{member.id}> is"

        rank = result.get('rank', 0)
        if rank <= 0:
            await interaction.followup.send(f"{member_name} ranked "
                                            f"{ordinal(result['rank'] + 1)} in the server")
        else:
            xp = result['xp']
            other_id = result['other_ID']
            other_xp = result['other_xp']
            other_name = result['other_name']
            await interaction.followup.send(f"{member_name} ranked "
                                            f"{ordinal(rank + 1)} in the server, "
                                            f"{round(other_xp - xp)} behind "
                                            f"<@{str(other_id)}> ({other_name})")

    @app_commands.command(name="leaderboard",
                          description="Shows the leaderboard of active members")
    @app_commands.describe(page="The page to display (default 1)",
                           threshold=f"The monthly xp needed to be listed "
                                     f"(default {RANK_DEFAULT_THRESHOLD})",
                           hidden="Hide from others in this server (default False)")
    async def leaderboard(self, interaction: discord.Interaction,
                          page: app_commands.Range[int, 1, RANK_MAX_PAGE] = 1,
                          threshold: app_commands.Range[int, 0] = RANK_DEFAULT_THRESHOLD,
                          hidden: bool = False):
        await interaction.response.defer(ephemeral=hidden)

        truerank = Truerank(threshold=threshold)
        description = ''
        page_start = (page - 1) * RANK_PAGE_SIZE
        page_end = page * RANK_PAGE_SIZE
        for index, item in enumerate(truerank.values[page_start:page_end]):
            description += f"\n**{index + 1 + page_start})**" \
                           f"<@{item['ID']}> - {round(item['xp'])} XP"
        if len(description) <= 0:
            await interaction.followup.send(":1234: This page does not exist")
            return
        description += f"\nPage: {page}/{ceil(len(truerank.values) / RANK_PAGE_SIZE)}"
        board = discord.Embed(title='Leaderboard',
                              description=description,
                              colour=discord.Colour.from_str(ACCENT_COLOUR))
        await interaction.followup.send(embed=board)

    @app_commands.command(name="user",
                          description="Shows details about the specified user")
    @app_commands.describe(user="The user to search for",
                           hidden="Hide from others in this server (default False)")
    async def user_info(self, interaction: discord.Interaction,
                        user: discord.User,
                        hidden: bool = False):
        await interaction.response.defer(ephemeral=hidden)

        # name, id, xp, level, rank

        member = resolve_member(interaction, user)
        if member is False:
            await interaction.followup.send(":bust_in_silhouette: "
                                            "That person in not in the server "
                                            "or hasn't reached level 15")
            return
        try:
            truerank = Truerank(threshold=RANK_DEFAULT_THRESHOLD)
            result = truerank.find_index(member.id)
        except IndexError:
            await interaction.followup.send(":bust_in_silhouette: "
                                            "That person has not been online "
                                            "recently enough")
            return

        id = user.id
        name = result['name']
        xp = result['xp']
        level = xp_to_lvl(xp)
        colour = result['colour']
        avatar = result['avatar']
        rank = result['rank']

        embed = discord.Embed(title=name,
                              colour=discord.Colour.from_str(colour))
        embed.add_field(name='User', value=f"<@{id}>")
        embed.add_field(name='XP', value=xp)
        embed.add_field(name='Level', value=level)
        embed.add_field(name='Rank', value=rank)
        embed.set_thumbnail(url=avatar)

        await interaction.followup.send(embed=embed)

    async def truerank_ctx(self, interaction: discord.Interaction,
                           member: discord.User):
        await interaction.response.defer(ephemeral=True)

        member = resolve_member(interaction, member)
        if member is False:
            await interaction.followup.send(":bust_in_silhouette: "
                                            "That person in not in the server "
                                            "or hasn't reached level 15")
            return
        try:
            truerank = Truerank(threshold=RANK_DEFAULT_THRESHOLD)
            result = truerank.find_index(member.id)
        except IndexError:
            await interaction.followup.send(":bust_in_silhouette: "
                                            "That person has not been online "
                                            "recently enough")
            return

        member_name = "You are" if member == interaction.user \
            else f"<@{member.id}> is"

        rank = result.get('rank', 0)
        if rank <= 0:
            await interaction.followup.send(f"{member_name} ranked "
                                            f"{ordinal(result['rank'] + 1)} in the server")
        else:
            xp = result['xp']
            other_id = result['other_ID']
            other_xp = result['other_xp']
            other_name = result['other_name']
            await interaction.followup.send(f"{member_name} ranked "
                                            f"{ordinal(rank + 1)} in the server, "
                                            f"{round(other_xp - xp)} behind "
                                            f"<@{str(other_id)}> ({other_name})")

    async def user_ctx(self, interaction: discord.Interaction,
                       member: discord.Member):
        await interaction.response.defer(ephemeral=True)

        member = resolve_member(interaction, member)
        if member is False:
            await interaction.followup.send(":bust_in_silhouette: "
                                            "That person in not in the server "
                                            "or hasn't reached level 15")
            return
        try:
            truerank = Truerank(threshold=RANK_DEFAULT_THRESHOLD)
            result = truerank.find_index(member.id)
        except IndexError:
            await interaction.followup.send(":bust_in_silhouette: "
                                            "That person has not been online "
                                            "recently enough")
            return

        id = member.id
        name = result['name']
        xp = result['xp']
        level = xp_to_lvl(xp)
        colour = result['colour']
        avatar = result['avatar']
        rank = result['rank']

        embed = discord.Embed(title=name,
                              colour=discord.Colour.from_str(colour))
        embed.add_field(name='User', value=f"<@{id}>")
        embed.add_field(name='XP', value=xp)
        embed.add_field(name='Level', value=level)
        embed.add_field(name='Rank', value=rank)
        embed.set_thumbnail(url=avatar)

        await interaction.followup.send(embed=embed)


async def setup(bot: commands.Bot):
    """
    Sets up the StatsCog and adds it to the bot.

    Args:
        bot (commands.Bot): The bot instance.
    """
    cog = StatsCog(bot)
    await bot.add_cog(cog, guilds=bot.guilds)
