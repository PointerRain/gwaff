import re
from typing import Any

import pandas as pd

from gwaff.database.db_base import BaseDatabase
from gwaff.database.structs import *
from gwaff.utils import request_api


class DatabaseMinecraft(BaseDatabase):
    """
    A class to handle Minecraft-related database operations.
    """

    def load_from_csv(self, data):
        """
        Loads Minecraft user data from a CSV file.

        Args:
            data (DataFrame): The data to load from the CSV file.
        """
        for index, row in data.iterrows():
            if (not pd.isna(row.iloc[0])) and (not pd.isna(row.iloc[1])):
                self.add_user(row.iloc[0], row.iloc[1])

        self.commit()

    def add_user(self, discord_id: int, mc_uuid: str, mc_name: str | None = None) -> None:
        """
        Adds or updates a Minecraft user in the database.

        Args:
            discord_id (int): The Discord ID of the user.
            mc_uuid (str): The Minecraft UUID of the user.
            mc_name (str, optional): The Minecraft name of the user. Defaults to None.
        """
        user = (self.session.query(MinecraftUser)
                .filter_by(discord_id=discord_id).first())
        if user is not None:
            user.mc_uuid = mc_uuid or user.mc_uuid  # pyright: ignore [reportAttributeAccessIssue]
            user.mc_name = mc_name or user.mc_name  # pyright: ignore [reportAttributeAccessIssue]
            return

        existing_user = (self.session.query(MinecraftUser)
                         .filter_by(mc_uuid=mc_uuid).first())
        if existing_user:
            print(f"User with mc_uuid {mc_uuid} already exists")
        #     self.session.delete(existing_user)

        new_user = MinecraftUser(discord_id=discord_id, mc_uuid=mc_uuid, mc_name=mc_name)
        self.session.add(new_user)

    def get_user(self, discord_id: int | None = None, mc_uuid: str | None = None) -> MinecraftUser | None:
        """
        Retrieves a Minecraft user from the database.

        Args:
            discord_id (int): The Discord ID of the user.
            mc_uuid (str): The Minecraft UUID of the user.

        Returns:
            MinecraftUser: The Minecraft user.
        """
        if not (discord_id or mc_uuid):
            return None
        user = self.session.query(MinecraftUser)
        if discord_id:
            user = user.filter_by(discord_id=discord_id)
        if mc_uuid:
            user = user.filter_by(mc_uuid=mc_uuid)
        return user.first()

    def get_users(self) -> list[MinecraftUser]:
        """
        Retrieves all Minecraft users from the database.

        Returns:
            list: A list of Minecraft users.
        """
        return (self.session.query(MinecraftUser)
                .join(Profile, MinecraftUser.discord_id == Profile.id).all())

    async def update_mc_name(self, discord_id, mc_uuid, mc_name=None):
        """
        Updates the Minecraft name of a user.

        Args:
            discord_id (int): The Discord ID of the user.
            mc_uuid (str): The Minecraft UUID of the user.
            mc_name (str, optional): The Minecraft name of the user. Defaults to None.

        Returns:
            bool: True if the update was successful, False otherwise.
        """
        try:
            data = request_api(
                f"https://sessionserver.mojang.com/session/minecraft/profile/{mc_uuid}")
            if data and (name := data.get('name')):
                if name != mc_name:
                    self.add_user(discord_id, mc_uuid, name)
                return True
            else:
                return False
        except Exception:
            return False

    async def update_all_mc_names(self):
        """
        Asynchronously updates the Minecraft names of all users.

        Returns:
            tuple: A tuple containing the number of successful updates and the total number of users.
        """
        users = self.session.query(MinecraftUser)
        success = 0
        total = 0
        for user in users:
            success += await self.update_mc_name(user.discord_id, user.mc_uuid, user.mc_name)
            total += 1
        self.commit()
        return success, total

    def to_json(self) -> list[dict]:
        """
        Exports Minecraft user data to a JSON object. Series of objects with keys
        'mc_name' and 'mc_uuid', and optional keys 'discord_nick' and 'colour'.
        'discord_nick' is included only if the Discord name is different from the Minecraft name.

        Returns:
            list: A list of Minecraft user data.
        """
        data: list[dict] = []

        for user in self.get_users():
            if user.mc_name is None:
                continue

            uuid = user.mc_uuid
            uuid = f'{uuid[0:8]}-{uuid[8:12]}-{uuid[12:16]}-{uuid[16:20]}-{uuid[20:32]}'
            colour: str = user.profile.colour.removeprefix('#')
            colours: list[str] = user.profile.colours.split(',') if user.profile.colours else []
            mc_name: str = str(user.mc_name)
            discord_nick = re.sub(' *\[.+]$', '', user.profile.name)

            entry: dict[str, Any] = {
                'mc_name': mc_name,
                'mc_uuid': uuid
            }

            if (re.sub('[ _.]', '', mc_name).lower() !=
                    re.sub('[ _.]', '', discord_nick).lower()
                    and len(discord_nick) >= 3):
                entry['discord_nick'] = discord_nick

            if colour not in {'95a5a6', '000000', 'ffffff', ''}:
                entry['colour'] = colour

            if len(colours) >= 2:
                entry['colours'] = [c.removeprefix('#') for c in colours]

            if len(entry) > 2:
                data.append(entry)
        return data

    def to_json_dict(self) -> dict[str, dict]:
        """
        Exports Minecraft user data to a JSON object. Dictionary with UUID keys and values
        containing keys 'mc_name' and 'mc_uuid', and optional keys 'discord_nick' and 'colour'.
        'discord_nick' is included only if the Discord name is different from the Minecraft name.

        Returns:
            dict: A dictionary of Minecraft user data.
        """
        data = {}

        for user in self.get_users():
            if user.mc_name is None:
                continue

            uuid = user.mc_uuid
            uuid = f'{uuid[0:8]}-{uuid[8:12]}-{uuid[12:16]}-{uuid[16:20]}-{uuid[20:32]}'
            colour: str = user.profile.colour.removeprefix('#')
            colours: list[str] = user.profile.colours.split(',') if user.profile.colours else []
            mc_name: str = str(user.mc_name)
            discord_nick = re.sub(' *\[.+]$', '', user.profile.name)

            entry: dict[str, Any] = {
                'mc_name': mc_name,
                'mc_uuid': uuid
            }

            if (re.sub('[ _.]', '', mc_name).lower() !=
                    re.sub('[ _.]', '', discord_nick).lower()
                    and len(discord_nick) >= 3):
                entry['nickname'] = discord_nick

            if colour not in {'95a5a6', '000000', 'ffffff'}:
                entry['colour'] = colour

            if len(colours) >= 2:
                entry['colours'] = [c.removeprefix('#') for c in colours]

            if len(entry) > 2:
                data[uuid] = entry
        return data


if __name__ == '__main__':
    dbm = DatabaseMinecraft()
    # dbm.load_from_csv(pd.read_csv("players.csv"))

    # for i in dbm.get_users():
    #     print(i.discord_id, i.profile.name, i.mc_name)

    # print(dbm.update_all_mc_names())

    # print(dbm.get_users())

    as_json = dbm.to_json()
    as_json_dict = dbm.to_json_dict()
    print(as_json)
    print(len(as_json))
    print(as_json_dict)
    print(len(as_json_dict))
