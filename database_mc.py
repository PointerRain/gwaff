import re

import pandas as pd

from database import BaseDatabase
from structs import *
from utils import request_api


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

    def add_user(self, discord_id, mc_uuid, mc_name=None):
        """
        Adds or updates a Minecraft user in the database.

        Args:
            discord_id (int): The Discord ID of the user.
            mc_uuid (str): The Minecraft UUID of the user.
            mc_name (str, optional): The Minecraft name of the user. Defaults to None.
        """
        user = (self.session.query(Minecraft)
                .filter_by(discord_id=discord_id).first())

        if user is not None:
            user.mc_uuid = mc_uuid or user.mc_uuid
            user.mc_name = mc_name or user.mc_name
            return

        print('Making new')
        new_user = Minecraft(discord_id=discord_id, mc_uuid=mc_uuid, mc_name=mc_name)
        self.session.add(new_user)

    def get_users(self):
        """
        Retrieves all Minecraft users from the database.

        Returns:
            list: A list of Minecraft users.
        """
        return self.session.query(Minecraft).join(Profile, Minecraft.discord_id == Profile.id).all()

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
            data = await request_api(
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
        users = self.session.query(Minecraft)
        success = 0
        total = 0
        for user in users:
            success += await self.update_mc_name(user.discord_id, user.mc_uuid, user.mc_name)
            total += 1
        self.commit()
        return success, total

    def to_json(self):
        """
        Exports Minecraft user data to a JSON file.

        Returns:
            int: The length of the JSON string.
        """
        data = []
        users = self.session.query(Minecraft).join(Profile,
                                                   Minecraft.discord_id == Profile.id).all()

        for user in users:
            if user.mc_name is None:
                continue

            uuid = user.mc_uuid
            uuid = f'{uuid[0:8]}-{uuid[8:12]}-{uuid[12:16]}-{uuid[16:20]}-{uuid[20:32]}'
            colour = user.profile.colour.replace('#', '')
            mc_name = user.mc_name
            discord_nick = user.profile.name
            if colour in ['95a5a6', '000000']:
                if re.sub('[ _.]', '', mc_name).lower() == re.sub('[ _.]', '',
                                                                  discord_nick).lower():
                    print(f"Skipping {user.mc_name}")
                    continue
            if colour == '000000':
                print(f"Skipping {user.mc_name}")
                continue
            data.append({
                'mc_name': user.mc_name,
                'mc_uuid': uuid,
                'discord_nick': user.profile.name,
                'colour': colour
            })
        return data


if __name__ == '__main__':
    dbm = DatabaseMinecraft()
    # dbm.load_from_csv(pd.read_csv("users_withnames.csv"))

    for i in dbm.get_users():
        print(i.discord_id, i.profile.name, i.mc_name)

    # print(dbm.update_all_mc_names())

    # print(dbm.get_users())

    print(dbm.to_json())
