import os
from datetime import datetime, timedelta
from time import mktime

import discord
from discord import app_commands
from discord.ext import commands

from gwaff.custom_logger import Logger
from gwaff.predictor import NoDataError, ZeroGrowthError, TargetBoundsError
from gwaff.predictor import TargetPrediction, xp_to_lvl, MAX_TARGET_DISTANCE, Forecast
from gwaff.utils import resolve_member, to_suffixed_number

logger = Logger('gwaff.bot.stats')

GRAPH_MAX_DAYS: int = int(os.environ.get("GRAPH_MAX_DAYS", 365))
PREDICTOR_DEFAULT_DAYS: int = int(os.environ.get("PREDICTOR_DEFAULT_DAYS", 30))
RANK_DEFAULT_THRESHOLD: int = int(os.environ.get("RANK_DEFAULT_THRESHOLD", 30))
RANK_MAX_PAGE: int = 5
RANK_PAGE_SIZE: int = 25
ACCENT_COLOUR: str = '#ea625e'


class PredictCog(commands.GroupCog, group_name='predict'):
    def __init__(self, bot: commands.Bot):
        self.bot = bot

    @app_commands.command(name="target",
                          description="Predict when you will pass a given level, "
                                      "xp, or member")
    @app_commands.describe(target='Either a level, xp, or member to aim for',
                           member='The member to do the prediction for'
                                  ' (default you)',
                           period='The period to average your growth over'
                                  ' (default 30 days)',
                           growth='Override the average daily growth calculation',
                           hidden='Hide from others in this server (default False)')
    async def predict_target(self, interaction: discord.Interaction,
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
            prediction = TargetPrediction(member=member.id,
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
                                        f"at a rate of {to_suffixed_number(prediction.growth)} "
                                        f"xp per day")

    @app_commands.command(name="forecast",
                          description="Predict what xp and level you will be at in the future")
    @app_commands.describe(days="The number of days in the future to predict for",
                           member='The member to do the prediction for'
                                  ' (default you)',
                           period='The period to average your growth over'
                                  ' (default 30 days)',
                           growth='Override the average daily growth calculation',
                           hidden='Hide from others in this server (default False)')
    async def predict_forecast(self, interaction: discord.Interaction,
                               days: app_commands.Range[int, 0, MAX_TARGET_DISTANCE],
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

        try:
            forecast = Forecast(member=member.id,
                                days=days,
                                period=period,
                                growth=growth)
            xp = forecast.evaluate()

        except ZeroGrowthError:
            await interaction.followup.send(":chart_with_downwards_trend: "
                                            "That person has earnt no xp recently")
            return
        except NoDataError:
            await interaction.followup.send(":mag: That target does not exist")
            return
        except Exception as e:
            await interaction.followup.send(f":question: An unknown error occurred:\n {e}")
            raise e

        date = mktime((datetime.now() + timedelta(days=days)).timetuple())
        member_name = "You" if member is interaction.user else f"<@{member.id}>"

        level = xp_to_lvl(xp)
        if xp <= 12017 or level > 100:
            await interaction.followup.send(f"{member_name} will have {to_suffixed_number(xp)} xp on "
                                            f"<t:{round(date)}:D> <t:{round(date)}:R> "
                                            f"at a rate of {to_suffixed_number(forecast.growth)} "
                                            f"xp per day")
            return

        await interaction.followup.send(f"{member_name} will be level {level} ({to_suffixed_number(xp)} xp) on "
                                        f"<t:{round(date)}:D> <t:{round(date)}:R> "
                                        f"at a rate of {to_suffixed_number(forecast.growth)} "
                                        f"xp per day")


async def setup(bot: commands.Bot):
    """
    Sets up the PredictCog and adds it to the bot.

    Args:
        bot (commands.Bot): The bot instance.
    """
    cog = PredictCog(bot)
    await bot.add_cog(cog, guilds=bot.guilds)
