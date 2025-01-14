import asyncio
from datetime import datetime
from typing import List, Optional, Union

from wechaty import (
    MessageType,
    FileBox,
    RoomMemberQueryFilter,
    Wechaty,
    Contact,
    Room,
    Message,
    Image,
    MiniProgram,
    Friendship,
    FriendshipType,
    EventReadyPayload
)
from wechaty_puppet import get_logger

logger = get_logger(__name__)


class MyBot(Wechaty):
    """
    A WeChat bot class inherited from Wechaty.
    """

    def __init__(self) -> None:
        """Initializes the bot."""
        super().__init__()
        self.login_user: Optional[Contact] = None

    async def on_ready(self, payload: EventReadyPayload) -> None:
        """Handles the on-ready event."""
        logger.info('Ready event: %s', payload)

    async def on_message(self, msg: Message) -> None:
        """Handles incoming messages."""
        from_contact: Contact = msg.talker()
        text: str = msg.text()
        room: Optional[Room] = msg.room()
        msg_type: MessageType = msg.type()

        if text == 'ding':
            conversation: Union[Room, Contact] = from_contact if room is None else room
            await conversation.ready()
            await conversation.say('dong')
            file_box = FileBox.from_url(
                'https://ss3.bdstatic.com/70cFv8Sh_Q1YnxGkpoWK1HF6hhy/it/'
                'u=1116676390,2305043183&fm=26&gp=0.jpg',
                name='ding-dong.jpg')
            await conversation.say(file_box)

        elif msg_type == MessageType.MESSAGE_TYPE_IMAGE:
            logger.info('Receiving image file')
            image: Image = msg.to_image()

            hd_file_box: FileBox = await image.hd()
            await hd_file_box.to_file('./hd-image.jpg', overwrite=True)

            thumbnail_file_box: FileBox = await image.thumbnail()
            await thumbnail_file_box.to_file('./thumbnail-image.jpg', overwrite=True)

            artwork_file_box: FileBox = await image.artwork()
            await artwork_file_box.to_file('./artwork-image.jpg', overwrite=True)

            await msg.say(hd_file_box)

        elif msg_type in [MessageType.MESSAGE_TYPE_AUDIO, MessageType.MESSAGE_TYPE_ATTACHMENT,
                          MessageType.MESSAGE_TYPE_VIDEO]:
            logger.info('Receiving file...')
            file_box = await msg.to_file_box()
            if file_box:
                await file_box.to_file(file_box.name)

        elif msg_type == MessageType.MESSAGE_TYPE_MINI_PROGRAM:
            logger.info('Receiving mini-program...')
            mini_program: Optional[MiniProgram] = await msg.to_mini_program()
            if mini_program:
                await msg.say(mini_program)

        elif text == 'get room members' and room:
            logger.info('Getting room members...')
            room_members: List[Contact] = await room.member_list()
            names: List[str] = [room_member.name for room_member in room_members]
            await msg.say('\n'.join(names))

        elif text.startswith('remove room member:'):
            logger.info('Removing room member...')
            if not room:
                await msg.say('This is not a room zone')
                return

            room_member_name = text[len('remove room member:') + 1:].strip()
            room_member: Optional[Contact] = await room.member(
                query=RoomMemberQueryFilter(name=room_member_name)
            )
            if room_member:
                if self.login_user and self.login_user.contact_id in room.payload.admin_ids:
                    await room.delete(room_member)
                else:
                    await msg.say('Login user is not the room admin')
            else:
                await msg.say(f'Cannot find room member by name <{room_member_name}>')

        elif text == 'get room topic' and room:
            logger.info('Getting room topic...')
            topic: Optional[str] = await room.topic()
            if topic:
                await msg.say(topic)

        elif text.startswith('rename room topic:') and room:
            logger.info('Renaming room topic...')
            new_topic = text[len('rename room topic:') + 1:].strip()
            await room.topic(new_topic)
            await msg.say(f'Room topic changed to: {new_topic}')

        elif text.startswith('add new friend:'):
            logger.info('Adding new friendship...')
            identity_info = text[len('add new friend:'):].strip()
            weixin_contact: Optional[Contact] = await self.Friendship.search(weixin=identity_info)
            phone_contact: Optional[Contact] = await self.Friendship.search(phone=identity_info)
            contact: Optional[Contact] = weixin_contact or phone_contact
            if contact:
                await self.Friendship.add(contact, 'hello world...')

        elif text == 'at me' and room:
            talker = msg.talker()
            await room.say('hello', mention_ids=[talker.contact_id])

        elif text == 'my alias':
            talker = msg.talker()
            alias = await talker.alias()
            await msg.say('Your alias is: ' + (alias or ''))

        elif text.startswith('set alias:'):
            talker = msg.talker()
            new_alias = text[len('set alias:'):].strip()
            await talker.alias(new_alias)
            alias = await talker.alias()
            await msg.say('Your new alias is: ' + (alias or ''))

        elif text.startswith('find friends:'):
            friend_name: str = text[len('find friends:'):].strip()
            friend = await self.Contact.find(friend_name)
            if friend:
                logger.info('Found friend: <%s>', friend)

            friends: List[Contact] = await self.Contact.find_all(friend_name)
            logger.info('Found friends count: <%d>', len(friends))
            logger.info(friends)

    async def on_login(self, contact: Contact) -> None:
        """Handles the login event."""
        logger.info('Contact <%s> has logged in...', contact)
        self.login_user = contact

    async def on_friendship(self, friendship: Friendship) -> None:
        """Handles friendship events."""
        MAX_ROOM_MEMBER_COUNT = 500
        if friendship.type() == FriendshipType.FRIENDSHIP_TYPE_RECEIVE:
            hello_text: str = friendship.hello()
            if 'wechaty' in hello_text.lower():
                await friendship.accept()
        elif friendship.type() == FriendshipType.FRIENDSHIP_TYPE_CONFIRM:
            wechaty_rooms: List[Room] = await self.Room.find_all('Wechaty')
            for wechaty_room in wechaty_rooms:
                members: List[Contact] = await wechaty_room.member_list()
                if len(members) < MAX_ROOM_MEMBER_COUNT:
                    contact: Contact = friendship.contact()
                    await wechaty_room.add(contact)
                    break

    async def on_room_join(self, room: Room, invitees: List[Contact], inviter: Contact, date: datetime) -> None:
        """Handles room join events."""
        names: List[str] = [invitee.name for invitee in invitees]
        await room.say(f'Welcome {", ".join(names)} to the WeChaty group!')


async def main() -> None:
    """Main function to run the bot."""
    bot = MyBot()
    await bot.start()


asyncio.run(main())
