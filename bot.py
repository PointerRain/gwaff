from typing import Optional, Any, Callable

import discord
from discord import app_commands, utils

import pandas as pd
from datetime import datetime, timedelta, timezone
import time
from math import ceil

from growth import Growth
from predictor import Prediction, xp_to_lvl, lvl_to_xp
from predictor import (NoDataError, ZeroGrowthError,
                       InvalidTargetError, TargetBoundsError)
from truerank import Truerank
from permissions import require_admin

GRAPH_MAX_DAYS: int = 365           # The maximum days that can be plotted on
                                    #  the gwaff/growth
GRAPH_DEFAULT_DAYS: int = 7         # The default days to be plotted on
                                    #  the gwaff/growth
GRAPH_MAX_USERS: int = 30           # The maximum number of users data to be
                                    #  plotted on the gwaff
GRAPH_DEFAULT_USERS: int = 15       # The default number of users to be
                                    #  plotted on the gwaff
COLLECTION_MAX_TIME: int = 120      # The maximum length of time that must go by
                                    #  before collection is said to be stopped.
PREDICTION_DEFAULT_DAYS: int = 30
RANK_DEFAULT_THRESHOLD: int = 30
RANK_MAX_PAGE: int = 5
RANK_PAGE_SIZE: int = 25
ACCENT_COLOUR: str = '#ea625e'

guilds = [
    discord.Object(id=1031086992403992576),
    discord.Object(id=1077927097739247727),
]
# guilds = []


class Gwaff(discord.Client):
    def __init__(self):
        intents = discord.Intents.default()
        super().__init__(intents=intents, activity=discord.Game(name='Gwaff'))
        self.synced = False
        self.servers = []

    async def on_ready(self) -> None:
        if not self.synced:
            await tree.sync()
            for server in self.guilds:
                await tree.sync(guild=discord.Object(id=server.id))
                print("[BOT] - " + server.name)
            self.synced = True
        print("[BOT] Ready!")


def growth(days: int = GRAPH_DEFAULT_DAYS,
           count: int = GRAPH_DEFAULT_USERS,
           member: discord.User = None,
           title: str = "Top chatters XP growth",
           special: bool = False,
           compare: discord.User = None) -> None:
    '''
    Plots and saves a growth plot (aka gwaff)

    '''
    if days >= GRAPH_MAX_DAYS:
        days = GRAPH_MAX_DAYS
    elif days <= 0:
        days = 0
    data = pd.read_csv("gwaff.csv", index_col=0)

    plot = Growth(data,
                  start_date=datetime.now() - timedelta(days=days),
                  special=special,
                  title=title)
    if member is None:
        include = None
        count = count
    else:
        include = [member.id]
        count = 1
    if compare is not None:
        include = [member.id, compare.id]
        count = 2
        plot.title = f"Comparing growth over the last {round(days)} days"
    plot.draw(max_count=count, include=include)
    plot.annotate()
    plot.configure()

    plot.save()
    plot.close()


def resolve_member(interaction: discord.Interaction,
                   user: discord.User) -> discord.User:
    if user is None and interaction is not None:
        return interaction.user
    data = pd.read_csv("gwaff.csv", index_col=0)
    if int(user.id) in data['ID'].unique():
        return user
    else:
        return False


def ordinal(n: int) -> str:
    suffixes = {1: "st", 2: "nd", 3: "rd"}
    i = n if (n < 20) else (n % 10)
    suffix = suffixes.get(i, 'th')
    return str(n) + suffix


bot = Gwaff()
tree = app_commands.CommandTree(bot)


@tree.command(name="gwaff",
              description="Plots top users growth")
@app_commands.describe(
    days=f'How many days to plot (default {GRAPH_DEFAULT_DAYS})',
    count=f'How many users to plot (default {GRAPH_DEFAULT_USERS})',
    hidden='Hide from others in this server (default False)')
async def plot_gwaff(interaction: discord.Interaction,
        days: app_commands.Range[float, 1, GRAPH_MAX_DAYS] = GRAPH_DEFAULT_DAYS,
        count: app_commands.Range[int, 1, GRAPH_MAX_USERS] = GRAPH_DEFAULT_USERS,
        hidden: bool = False):
    # if interaction.user.id in [344731282095472641]:
    #     await interaction.response.defer(ephemeral=hidden)
    #     growth(days=days, count=count, special=True)
    #     await interaction.followup.send(file=discord.File('out.png'))
    # else:
    #     await interaction.followup.send(":no_entry: You can't use this command",
    #                                     ephemeral=True)
    await interaction.response.defer(ephemeral=hidden)

    title: str;
    if days == GRAPH_DEFAULT_DAYS:
        title = "Top chatters XP growth"
    else:
        title = f"Top chatters XP over the last {round(days)} days"
    growth(days=days, count=count, title=title, special=True)
    await interaction.followup.send(file=discord.File('out.png'))


# @tree.command(name="daily",
#               description="Plots the last 24 hours of growth")
# @app_commands.describe(hidden='Hide from others in this server (default False)')
# async def plot_daily(interaction: discord.Interaction, hidden: bool = False):
#     await interaction.response.defer(ephemeral=hidden)
#     growth(days=1, special=True, title="Top chatters of the last 24 hours")
#     await interaction.followup.send(file=discord.File('out.png'))


@tree.command(name="data",
              description="Gets the entire gwaff data as a csv")
@app_commands.describe(hidden='Hide from others in this server (default True)')
@require_admin
async def send_data(interaction: discord.Interaction, hidden: bool = True):
    await interaction.followup.send(file=discord.File('gwaff.csv'), ephemeral=hidden)


@tree.command(name="last",
              description="Sends the last plot.")
@app_commands.describe(hidden='Hide from others in this server (default False)')
@require_admin
async def send_data(interaction: discord.Interaction, hidden: bool = False):
    await interaction.followup.send(file=discord.File('out.png'), ephemeral=hidden)


@tree.command(name="isalive",
              description="When did I last collect data")
@app_commands.describe(hidden='Hide from others in this server (default True)')
async def is_alive(interaction: discord.Interaction, hidden: bool = True):
    await interaction.response.defer(ephemeral=hidden)

    now = datetime.now()

    data = pd.read_csv("gwaff.csv", index_col=0)
    plot = Growth(data)

    last = plot.dates[-1]
    last = datetime.fromisoformat(last)
    laststr = utils.format_dt(last, 'R')

    prevlast = plot.dates[-2]
    prevlast = datetime.fromisoformat(prevlast)
    prevlaststr = utils.format_dt(prevlast, 'R')

    alive: str;
    if (now - last).total_seconds() < 1.1 * COLLECTION_MAX_TIME*60:
        alive = ""
    else:
        alive = "Collection has halted!"
    await interaction.followup.send(f"Data was last collected {laststr}\n"
                                    f"(Before that {prevlaststr})\n{alive}")


'''
@tree.command(name="reduce")
async def send_data(interaction: discord.Interaction):
    if interaction.user.id in [344731282095472641]:
        await interaction.response.defer(ephemeral=True)
        start_size = 0
        reduce()
        end_size = 0
        await interaction.followup.send(f"Reduced filesize by "
                                        f"{end_size-start_size}!")
    else:
        await interaction.followup.send(":no_entry: You can't use this command",
                                        ephemeral=True)
'''


@tree.command(name="predict",
              description="Predict when you will pass a given level, "
                          "xp, or member")
@app_commands.describe(target='Either a level, xp, or member to aim for',
                       member='The member to do the prediction for'
                              ' (default you)',
                       period='The period to average your growth over'
                              ' (default 30 days)',
                       growth='Override the average daily growth calculation',
                       hidden='Hide from others in this server (default False)')
async def predict(interaction: discord.Interaction,
                  target: str,
                  member: discord.User = None,
                  period: app_commands.Range[int, 1, GRAPH_MAX_DAYS] = PREDICTION_DEFAULT_DAYS,
                  growth: int = None,
                  hidden: bool = False):
    await interaction.response.defer(ephemeral=hidden)

    data = pd.read_csv("gwaff.csv", index_col=0)
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
        prediction = Prediction(data,
                                member=member.id,
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
        return

    date = time.mktime((datetime.now() + timedelta(days=days)).timetuple())
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


@tree.command(name="growth",
              description="Plots a specific member's growth")
@app_commands.describe(member="The member plot (default you)",
                       days="How many days to plot (default 7)",
                       compare="A second user to show",
                       hidden="Hide from others in this server (default False)")
async def plot_growth(interaction: discord.Interaction,
                      member: discord.User = None,
                      days: app_commands.Range[float, 1, GRAPH_MAX_DAYS] = GRAPH_DEFAULT_DAYS,
                      compare: discord.User = None,
                      hidden: bool = False):
    await interaction.response.defer(ephemeral=hidden)
    member = resolve_member(interaction, member)
    if member is False:
        await interaction.followup.send(":bust_in_silhouette: "
                                        "That person in not in the server "
                                        "or hasn't reached level 15")
        return

    co_member: discord.User;
    if compare:
        co_member = resolve_member(None, compare)
        if co_member is False:
            await interaction.followup.send(":bust_in_silhouette: "
                                            "That person in not in the server "
                                            "or hasn't reached level 15")
            return
    else:
        co_member = None

    try:
        growth(days=days, member=member, count=1,
               title=f"{member.name}'s growth over the last {round(days)} days",
               compare=co_member)
    except IndexError:
        await interaction.followup.send(":bust_in_silhouette: "
                                        "That person has not been online "
                                        "recently enough")
        return
    await interaction.followup.send(file=discord.File('out.png'))


@tree.command(name="truerank",
              description="Tells you your position out of only active members")
@app_commands.describe(member='The member to check (default you)',
                       threshold=f"The monthly xp needed to be listed "
                                 f"(default {RANK_DEFAULT_THRESHOLD})",
                       hidden='Hide from others in this server (default False)')
async def rank_true(interaction: discord.Interaction,
                    member: discord.User = None,
                    threshold: int = RANK_DEFAULT_THRESHOLD,
                    hidden: bool = False):
    await interaction.response.defer(ephemeral=hidden)

    data = pd.read_csv("gwaff.csv", index_col=0)
    member = resolve_member(interaction, member)
    if member is False:
        await interaction.followup.send(":bust_in_silhouette: "
                                        "That person in not in the server "
                                        "or hasn't reached level 15")
        return
    try:
        truerank = Truerank(data, threshold=threshold)
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
                                        f"{ordinal(result['rank']+1)} in the server")
    else:
        xp = result['xp']
        other_id = result['other_ID']
        other_xp = result['other_xp']
        other_name = result['other_name']
        await interaction.followup.send(f"{member_name} ranked "
                                        f"{ordinal(rank+1)} in the server, "
                                        f"{round(other_xp - xp)} behind "
                                        f"<@{str(other_id)}> ({other_name})")


@tree.command(name="leaderboard",
              description="Shows the leaderboard of active members")
@app_commands.describe(page="The page to display (default 1)",
                       threshold=f"The monthly xp needed to be listed "
                       f"(default {RANK_DEFAULT_THRESHOLD})",
                       hidden="Hide from others in this server (default False)")
async def leaderboard(interaction: discord.Interaction,
                      page: app_commands.Range[int, 1, RANK_MAX_PAGE] = 1,
                      threshold: app_commands.Range[int, 0] = RANK_DEFAULT_THRESHOLD,
                      hidden: bool = False):
    await interaction.response.defer(ephemeral=hidden)

    data = pd.read_csv("gwaff.csv", index_col=0)
    truerank = Truerank(data, threshold=threshold)
    description = ''
    page_start = (page-1) * RANK_PAGE_SIZE
    page_end = page * RANK_PAGE_SIZE
    for index, item in enumerate(truerank.values[page_start:page_end]):
        description += f"\n**{index + 1 + page_start})**" \
            f"<@{item['ID']}> ({item['name']})" \
            f"({round(item['xp'])} XP)"
    if len(description) <= 0:
        await interaction.followup.send(":1234: This page does not exist")
        return
    description += f"\nPage: {page}/{ceil(len(truerank.values) / RANK_PAGE_SIZE)}"
    board = discord.Embed(title='Leaderboard',
                          description=description,
                          colour=discord.Colour.from_str(ACCENT_COLOUR))
    await interaction.followup.send(embed=board)


@tree.command(name="user",
              description="Shows details about the specified user")
@app_commands.describe(user="The user to search for",
                       hidden="Hide from others in this server (default False)")
async def user_info(interaction: discord.Interaction,
                    user: discord.Member,
                    hidden: bool = False):
    await interaction.response.defer(ephemeral=hidden)

    # name, id, xp, level, rank

    data = pd.read_csv("gwaff.csv", index_col='ID')
    member = resolve_member(interaction, user)
    if member is False:
        await interaction.followup.send(":bust_in_silhouette: "
                                        "That person in not in the server "
                                        "or hasn't reached level 15")
        return
    try:
        truerank = Truerank(data, threshold=30)
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
    url = result['url']
    rank = result['rank']

    embed = discord.Embed(title=name,
                          colour=discord.Colour.from_str('#ea625e'))
    embed.add_field(name='User', value=f"<@{id}>")
    embed.add_field(name='XP', value=xp)
    embed.add_field(name='Level', value=level)
    embed.add_field(name='Rank', value=rank)
    embed.set_thumbnail(url=url)

    await interaction.followup.send(embed=embed)


@tree.command(name="ping", description="Pong!")
async def ping(interaction: discord.Interaction):
    now = datetime.now(timezone.utc)
    msgtime = interaction.created_at
    ping = (now - msgtime).total_seconds() * 2000.0
    print("[BOT] Ping:", ping)
    await interaction.response.send_message(f"Pong!\n{round(ping)} ms",
                                            ephemeral=True)


@tree.context_menu(name='Growth')
async def growth_ctx(interaction: discord.Interaction, member: discord.Member):
    await interaction.response.defer(ephemeral=True)
    member = resolve_member(interaction, user)
    if member is False:
        await interaction.followup.send(":bust_in_silhouette: "
                                        "That person in not in the server "
                                        "or hasn't reached level 15")
        return
    try:
        growth(days=GRAPH_DEFAULT_DAYS, member=member, count=1,
               title=f"{member.name}'s growth over the last {round(days)} days")
    except IndexError:
        await interaction.followup.send(":bust_in_silhouette: "
                                        "That person has not been online "
                                        "recently enough")
        return
    await interaction.followup.send(file=discord.File('out.png'))


@tree.context_menu(name='True Rank')
async def truerank_ctx(interaction: discord.Interaction,
                       member: discord.Member):
    await interaction.response.defer(ephemeral=True)

    data = pd.read_csv("gwaff.csv", index_col=0)
    member = resolve_member(interaction, member)
    if member is False:
        await interaction.followup.send(":bust_in_silhouette: "
                                        "That person in not in the server "
                                        "or hasn't reached level 15")
        return
    try:
        truerank = Truerank(data, threshold=RANK_DEFAULT_THRESHOLD)
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
                                        f"{ordinal(result['rank']+1)} in the server")
    else:
        xp = result['xp']
        other_id = result['other_ID']
        other_xp = result['other_xp']
        other_name = result['other_name']
        await interaction.followup.send(f"{member_name} ranked "
                                        f"{ordinal(rank+1)} in the server, "
                                        f"{round(other_xp - xp)} behind "
                                        f"<@{str(other_id)}> ({other_name})")


def run_the_bot(token) -> None:
    '''
    Runs the bot
    '''

    bot.run(token)


if __name__ == '__main__':
    print("[ERROR][BOT] Need to run through run_the_bot with the token!")
    exit()
