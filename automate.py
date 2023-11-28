import discord
from discord import app_commands, utils

from growth import Growth
import pandas as pd
from datetime import datetime, timedelta, timezone
import time
from math import ceil

from predictor import Prediction, xp_to_lvl, lvl_to_xp
from truerank import Truerank

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

    async def on_ready(self):
        if not self.synced:
            await tree.sync()
            for server in client.guilds:
                await tree.sync(guild=discord.Object(id=server.id))
                print("[BOT] - " + server.name)
            self.synced = True
        print("[BOT] Ready!")


def growth(days=7, count: int = 15, member=None, title="Top chatters XP growth",
           special=False, compare=None):
    '''
    Plots and saves a growth plot (aka gwaff)

    '''
    if days >= 365:
        days = 365
    elif days <= 0:
        days = 0
    data = pd.read_csv("gwaff.csv", index_col=0)

    plot = Growth(data,
                  start_date=datetime.now() - timedelta(days=days),
                  special=special,
                  title=title)
    if member is None:
        include = None
        count = 15
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


def resolve_member(interaction, user):
    if user is None and interaction is not None:
        return interaction.user
    data = pd.read_csv("gwaff.csv", index_col=0)
    if int(user.id) in data['ID'].unique():
        return user
    else:
        return False


def ordinal(n):
    suffixes = {1: "st", 2: "nd", 3: "rd"}
    i = n if (n < 20) else (n % 10)
    suffix = suffixes.get(i, 'th')
    return str(n) + suffix


client = Gwaff()
tree = app_commands.CommandTree(client)


@tree.command(name="gwaff",
              description="Plots top users growth")
@app_commands.describe(days='How many days to plot (default 7)',
                       count='How many users to plot (default 15)',
                       hidden='Hide from others in this server (default True)')
async def plot_gwaff(interaction: discord.Interaction,
                     days: app_commands.Range[float, 0, 365] = 7,
                     count: int = 15,
                     hidden: bool = True):
    now = datetime.now()
    if interaction.user.id in [344731282095472641]:
        await interaction.response.defer(ephemeral=hidden)
        growth(days=days, count=count, special=True)
        await interaction.followup.send(file=discord.File('out.png'))
    else:
        await interaction.followup.send(":no_entry: You can't use this command",
                                        ephemeral=True)


@tree.command(name="daily",
              description="Plots the last 24 hours of growth")
@app_commands.describe(hidden='Hide from others in this server (default False)')
async def plot_daily(interaction: discord.Interaction, hidden: bool = False):
    await interaction.response.defer(ephemeral=hidden)
    growth(days=1, special=True, title="Top chatters of the last 24 hours")
    await interaction.followup.send(file=discord.File('out.png'))


@tree.command(name="data",
              description="Gets the entire gwaff data as a csv")
@app_commands.describe(hidden='Hide from others in this server (default True)')
async def send_data(interaction: discord.Interaction, hidden: bool = True):
    await interaction.response.defer(ephemeral=hidden)
    if interaction.user.id in [344731282095472641]:
        await interaction.followup.send(file=discord.File('gwaff.csv'))
    else:
        await interaction.followup.send(":no_entry: You can't use this command")


@tree.command(name="isalive",
              description="When did I last collect data")
@app_commands.describe(hidden='Hide from others in this server (default True)')
async def last_record(interaction: discord.Interaction, hidden: bool = True):
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

    alive = "" if (now - last).total_seconds() < 1.1 * \
        120*60 else "Collection has halted!"
    await interaction.followup.send(f"Data was last collected {laststr}\n"
                                    f"(Before that {prevlaststr})\n{alive}")


'''
@tree.command(name="reduce")
async def send_data(interaction: discord.Interaction):
    if interaction.user.id in [344731282095472641]:
        await interaction.response.defer(ephemeral=True)
        startsize = 0
        reduce()
        endsize = 0
        await interaction.followup.send("Reduced filesize by "+str(endsize-startsize)+"!")
    else:
        await interaction.followup.send(":no_entry: You can't use this command",
                                        ephemeral=True)
'''


@tree.command(name="predict",
              description="Predict when you will pass a given level,"
                          " xp, or member")
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
                  period: int = 30,
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
    except ZeroDivisionError:
        await interaction.followup.send(":mirror: "
                                        "The target cannot be the same as "
                                        "the member")
        return
    except IndexError:
        await interaction.followup.send(":mag: That target does not exist")
        return
    except Exception as e:
        await interaction.followup.send(":question: An unknown error occured")
        raise e
        return
    if days == 'target':
        await interaction.followup.send(f":x: Invalid target {target}")
        return
    if days >= 100 * 365:
        await interaction.followup.send(":telescope: "
                                        "That target is too far away")
        return
    if days != days:
        await interaction.followup.send(":question: An unknown error occured")
        return

    date = time.mktime((datetime.now() + timedelta(days=days)).timetuple())
    member_name = "You" if member == interaction.user else f"<@{member.id}>"

    if prediction.target_type == 'xp':
        target = str(prediction.target) + ' xp'
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
                      days: app_commands.Range[float, 0, 365] = 7,
                      compare: discord.User = None,
                      hidden: bool = False):
    await interaction.response.defer(ephemeral=hidden)
    member = resolve_member(interaction, member)
    if member is False:
        await interaction.followup.send(":bust_in_silhouette: "
                                        "That person in not in the server "
                                        "or hasn't reached level 15")
        return
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
                       hidden='Hide from others in this server (default False)')
async def rank_true(interaction: discord.Interaction,
                    member: discord.User = None,
                    threshold: int = 30,
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
        rank = Truerank(data, threshold=threshold)
        index, xp, other, other_xp, other_name = rank.find_index(member.id)
    except IndexError:
        await interaction.followup.send(":bust_in_silhouette: "
                                        "That person has not been online "
                                        "recently enough")
        return

    member_name = "You are" if member == interaction.user \
                  else f"<@{member.id}> is"

    if other_xp - xp <= 0:
        await interaction.followup.send(f"{member_name} ranked "
                                        f"{ordinal(index+1)} in the server")
    else:
        await interaction.followup.send(f"{member_name} ranked "
                                        f"{ordinal(index+1)} in the server "
                                        f"({round(other_xp - xp)} behind "
                                        f"<@{str(other)}>)")


@tree.command(name="leaderboard",
              description="Shows the leaderboard of active members")
@app_commands.describe(page="The page to display (default 1)",
                       threshold="The monthly xp needed to be listed "
                                 "(default 30)",
                       hidden="Hide from others in this server (default False)")
async def leaderboard(interaction: discord.Interaction,
                      page: int = 1,
                      threshold: int = 30,
                      hidden: bool = False):
    await interaction.response.defer(ephemeral=hidden)

    data = pd.read_csv("gwaff.csv", index_col=0)
    rank = Truerank(data, threshold=threshold)
    description = ''
    for index, item in enumerate(rank.values[(page - 1) * 25:page * 25]):
        description += f"\n**{index+1+(page-1)*25})** <@{item[0]}> "
        f"({round(item[2])} XP)"
    if len(description) <= 0:
        await interaction.followup.send(":1234: This page does not exist")
        return
    description += f"\nPage: {page}/{ceil(len(rank.values) / 25)}"
    board = discord.Embed(title='Leaderboard',
                          description=description,
                          colour=discord.Colour.from_str('#ea625e'))
    await interaction.followup.send(embed=board)


@tree.command(name="ping", description="Pong!")
async def ping(interaction: discord.Interaction):
    now = datetime.now(timezone.utc)
    msgtime = interaction.created_at
    ping = (now - msgtime).total_seconds() * 2000.0
    print("[BOT] Ping:", ping)
    await interaction.response.send_message(f"Pong!\n {round(ping)} ms",
                                            ephemeral=True)


@tree.context_menu(name='Growth')
async def growth_ctx(interaction: discord.Interaction, user: discord.Member):
    await interaction.response.defer(ephemeral=True)
    member = resolve_member(interaction, user)
    if member is False:
        await interaction.followup.send(":bust_in_silhouette: "
                                        "That person in not in the server "
                                        "or hasn't reached level 15")
        return
    try:
        growth(days=7, member=member, count=1,
               title=f"{member.name}'s growth over the last {round(days)} days")
    except IndexError:
        await interaction.followup.send(":bust_in_silhouette: "
                                        "That person has not been online "
                                        "recently enough")
        return
    await interaction.followup.send(file=discord.File('out.png'))


@tree.context_menu(name='True Rank')
async def truerank_ctx(interaction: discord.Interaction, user: discord.Member):
    await interaction.response.defer(ephemeral=True)

    data = pd.read_csv("gwaff.csv", index_col=0)
    member = resolve_member(interaction, user)
    if member is False:
        await interaction.followup.send(":bust_in_silhouette: "
                                        "That person in not in the server "
                                        "or hasn't reached level 15")
        return
    rank = Truerank(data, threshold=30)
    index, xp, other, other_xp, other_name = rank.find_index(member.id)

    member_name = "You are" if member == interaction.user \
                  else f"<@{member.id}> is"

    if other_xp - xp <= 0:
        await interaction.followup.send(f"{member_name} ranked "
                                        f"{ordinal(index+1)} in the server")
    else:
        await interaction.followup.send(f"{member_name} ranked "
                                        f"{ordinal(index+1)} in the server "
                                        f"({round(other_xp - xp)} behind "
                                        f"<@{str(other)}>)")


def runTheBot(token):
    client.run(token)


if __name__ == '__main__':
    print("[ERROR][BOT] Need to run through runTheBot with the token!")
    exit()
