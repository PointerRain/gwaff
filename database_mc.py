import pandas as pd
import json

from structs import *
from utils import request_api

class DatabaseMinecraft(BaseDatabase):
    def load_from_csv(self, data):
        for index, row in data.iterrows():
            self.add_user(row.iloc[0], row.iloc[1])

        self.commit()

    def add_user(self, discord_id, mc_uuid, mc_name=None):
        if pd.isna(mc_uuid):
            return

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
        return self.session.query(Minecraft).join(Profile, Minecraft.discord_id == Profile.id).all()

    def find_mc_name(self, discord_id, mc_uuid, mc_name=None):
        try:
            data = request_api(f"https://sessionserver.mojang.com/session/minecraft/profile/{mc_uuid}")
            if data and (name := data.get('name')):
                print(name)
                if name != mc_name:
                    self.add_user(discord_id, mc_uuid, name)
                return True
            else:
                print('COULDNT FIND IT')
                return False
        except Exception as e:
            print('AN ERROR OCCURED:', e)
            return False

    def find_all_mc_names(self):
        users = self.session.query(Minecraft)
        changed, kept, failed = (0,0,0)
        for user in users:
            self.find_mc_name(user.discord_id, user.mc_uuid, user.mc_name)
        self.commit()
        return (changed, kept, failed)

    def to_json(self):
        data = []
        users = self.session.query(Minecraft).join(Profile, Minecraft.discord_id == Profile.id).all()
        for user in users:
            if user.mc_name is None:
                continue

            uuid = user.mc_uuid
            uuid = f'{uuid[0:8]}-{uuid[8:12]}-{uuid[12:16]}-{uuid[16:20]}-{uuid[20:32]}'
            # colour = None
            # if discord_id in STAFF_LIST:
            #     colour = None
            #     # if discord_id in ADMIN_LIST:
            #     #     colour = '5077F5'
            #     # elif discord_id in MOD_LIST:
            #     #     colour = '00A31E'
            #     # elif discord_id in HELPER_LIST:
            #     #     colour = '00AC7E'
            # else:
            colour = user.profile.colour.replace('#', '')
            data.append({
                'mc_name': user.mc_name,
                'mc_uuid': uuid,
                'discord_id': user.discord_id,
                'discord_nick': user.profile.name,
                'colour': colour
            })
        with open('minecraft.txt', 'w', encoding='utf-8') as f:
            json.dump(data, f)
        return len(str(data))