import discord

from datetime import datetime, timedelta
import pandas as pd

from growth import Growth

GRAPH_MAX_DAYS: int = 365           # The maximum days that can be plotted on
                                    #  the gwaff/growth
GRAPH_DEFAULT_DAYS: int = 7         # The default days to be plotted on
                                    #  the gwaff/growth
GRAPH_MAX_USERS: int = 30           # The maximum number of users data to be
                                    #  plotted on the gwaff
GRAPH_DEFAULT_USERS: int = 15       # The default number of users to be
                                    #  plotted on the gwaff

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