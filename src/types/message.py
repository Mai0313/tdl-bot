from pydantic import Field, BaseModel


class CaptionEntity(BaseModel):
    length: int = Field(
        ...,
        title="Entity Length",
        description="The length of the entity in characters.",
        deprecated=False,
        examples=[4],
    )
    offset: int = Field(
        ...,
        title="Entity Offset",
        description="The offset in characters to the start of the entity.",
        deprecated=False,
        examples=[0],
    )
    type: str = Field(
        ...,
        title="Entity Type",
        description="The type of entity (e.g., hashtag, mention).",
        deprecated=False,
        examples=["hashtag"],
    )


class ForwardFromChat(BaseModel):
    id: int = Field(
        ...,
        title="Chat ID",
        description="Unique identifier for the chat.",
        deprecated=False,
        examples=[-1001981059724],
    )
    title: str = Field(
        ...,
        title="Chat Title",
        description="Title of the chat.",
        deprecated=False,
        examples=["晚间休息室🔞"],
    )
    username: str = Field(
        ...,
        title="Chat Username",
        description="Username of the chat.",
        deprecated=False,
        examples=["wanjianxiuxishi"],
    )
    type: str = Field(
        ...,
        title="Chat Type",
        description="Type of chat (e.g., private, group, channel).",
        deprecated=False,
        examples=["channel"],
    )


class ForwardOriginChat(BaseModel):
    id: int = Field(
        ...,
        title="Forwarded Chat ID",
        description="Unique identifier for the forwarded chat.",
        deprecated=False,
        examples=[-1001981059724],
    )
    title: str = Field(
        ...,
        title="Forwarded Chat Title",
        description="Title of the forwarded chat.",
        deprecated=False,
        examples=["晚间休息室🔞"],
    )
    type: str = Field(
        ...,
        title="Forwarded Chat Type",
        description="Type of the forwarded chat (e.g., channel).",
        deprecated=False,
        examples=["channel"],
    )
    username: str | None = Field(
        default=None,
        title="Forwarded Chat Username",
        description="Username of the forwarded chat.",
        deprecated=False,
        examples=["wanjianxiuxishi"],
    )


class ForwardOrigin(BaseModel):
    chat: ForwardOriginChat = Field(
        ...,
        title="Forwarded Origin Chat",
        description="Chat object of the original forwarded chat.",
        deprecated=False,
    )
    message_id: int = Field(
        ...,
        title="Forwarded Message ID",
        description="Identifier of the forwarded message.",
        deprecated=False,
        examples=[156],
    )
    date: int = Field(
        ...,
        title="Forwarded Date",
        description="Date of the forwarded message in Unix time.",
        deprecated=False,
        examples=[1717832693],
    )
    type: str = Field(
        ...,
        title="Forwarded Message Type",
        description="Type of the forwarded message origin.",
        deprecated=False,
        examples=["channel"],
    )


class PhotoSize(BaseModel):
    height: int = Field(
        ...,
        title="Photo Height",
        description="Height of the photo.",
        deprecated=False,
        examples=[90],
    )
    width: int = Field(
        ...,
        title="Photo Width",
        description="Width of the photo.",
        deprecated=False,
        examples=[48],
    )
    file_id: str = Field(
        ...,
        title="Photo File ID",
        description="Unique identifier for the photo file.",
        deprecated=False,
        examples=[
            "AgACAgEAAxkBAAMjZw6gU671et6SfroS-lu3AAF2a4kzAAIKrDEbdD0hRwiI5gUEiNK7AQADAgADcwADNgQ"
        ],
    )
    file_size: int = Field(
        ...,
        title="Photo File Size",
        description="File size of the photo in bytes.",
        deprecated=False,
        examples=[1071],
    )
    file_unique_id: str = Field(
        ...,
        title="Unique Photo File ID",
        description="Unique identifier for the photo file that is constant over time.",
        deprecated=False,
        examples=["AQADCqwxG3Q9IUd4"],
    )


class Chat(BaseModel):
    first_name: str | None = Field(
        default=None,
        title="First Name",
        description="First name of the user or chat.",
        deprecated=False,
        examples=["Well"],
    )
    id: int = Field(
        ...,
        title="Chat ID",
        description="Unique identifier for this chat.",
        deprecated=False,
        examples=[5727382280],
    )
    type: str = Field(
        ...,
        title="Chat Type",
        description="Type of chat (e.g., private, group).",
        deprecated=False,
        examples=["private"],
    )


class FromUser(BaseModel):
    first_name: str | None = Field(
        default=None,
        title="First Name",
        description="First name of the user.",
        deprecated=False,
        examples=["Well"],
    )
    id: int = Field(
        ...,
        title="User ID",
        description="Unique identifier for this user.",
        deprecated=False,
        examples=[5727382280],
    )
    is_bot: bool = Field(
        ...,
        title="Is Bot",
        description="True if this user is a bot.",
        deprecated=False,
        examples=[False],
    )
    is_premium: bool = Field(
        ...,
        title="Is Premium User",
        description="True if this user has a premium account.",
        deprecated=False,
        examples=[True],
    )
    language_code: str | None = Field(
        default=None,
        title="Language Code",
        description="IETF language tag of the user's language.",
        deprecated=False,
        examples=["en"],
    )


class Message(BaseModel):
    caption: str | None = Field(
        default=None,
        title="Caption",
        description="Caption for the message, if any.",
        deprecated=False,
        examples=["#FC2-PPV-4409072"],
    )
    caption_entities: list[CaptionEntity] | None = Field(
        default=None,
        title="Caption Entities",
        description="List of entities in the caption.",
        deprecated=False,
        examples=[[{"length": 4, "offset": 0, "type": "hashtag"}]],
    )
    channel_chat_created: bool = Field(
        ...,
        title="Channel Chat Created",
        description="True if the channel chat was created.",
        deprecated=False,
        examples=[False],
    )
    delete_chat_photo: bool = Field(
        ...,
        title="Delete Chat Photo",
        description="True if the chat photo should be deleted.",
        deprecated=False,
        examples=[False],
    )
    forward_origin: ForwardOrigin | None = Field(
        default=None,
        title="Forwarded Origin",
        description="Origin of the forwarded message, if any.",
        deprecated=False,
        examples=[
            {
                "chat": {
                    "id": -1001981059724,
                    "title": "晚间休息室🔞",
                    "type": "channel",
                    "username": "wanjianxiuxishi",
                },
                "message_id": 156,
                "date": 1717832693,
                "type": "channel",
            }
        ],
    )
    group_chat_created: bool = Field(
        ...,
        title="Group Chat Created",
        description="True if the group chat was created.",
        deprecated=False,
        examples=[False],
    )
    media_group_id: str | None = Field(
        default=None,
        title="Media Group ID",
        description="The media group ID for photos and videos.",
        deprecated=False,
        examples=["13832104940757477"],
    )
    photo: list[PhotoSize] | None = Field(
        default=None,
        title="Photos",
        description="List of available photos with different sizes.",
        deprecated=False,
        examples=[
            [
                {
                    "height": 90,
                    "width": 48,
                    "file_id": "AgACAgEAAxkBAAMjZw6gU671et6SfroS-lu3AAF2a4kzAAIKrDEbdD0hRwiI5gUEiNK7AQADAgADcwADNgQ",
                    "file_size": 1071,
                    "file_unique_id": "AQADCqwxG3Q9IUd4",
                }
            ]
        ],
    )
    supergroup_chat_created: bool = Field(
        ...,
        title="Supergroup Chat Created",
        description="True if the supergroup chat was created.",
        deprecated=False,
        examples=[False],
    )
    chat: Chat = Field(
        ..., title="Chat", description="Chat object that represents the chat.", deprecated=False
    )
    date: int = Field(
        ...,
        title="Date",
        description="Date the message was sent in Unix time.",
        deprecated=False,
        examples=[1729013117],
    )
    message_id: int = Field(
        ...,
        title="Message ID",
        description="Unique message identifier inside this chat.",
        deprecated=False,
        examples=[97],
    )
    from_user: FromUser | None = Field(
        default=None,
        title="From User",
        description="Sender of the message, if sent by a user.",
        deprecated=False,
        examples=[
            {
                "first_name": "Well",
                "id": 5727382280,
                "is_bot": False,
                "is_premium": True,
                "language_code": "en",
            }
        ],
    )
    forward_date: int | None = Field(
        default=None,
        title="Forward Date",
        description="Date the original message was sent in Unix time.",
        deprecated=False,
        examples=[1717832693],
    )
    forward_from_chat: ForwardFromChat | None = Field(
        default=None,
        title="Forwarded From Chat",
        description="Chat from which the message was forwarded.",
        deprecated=False,
        examples=[
            {
                "id": -1001981059724,
                "title": "晚间休息室🔞",
                "username": "wanjianxiuxishi",
                "type": "channel",
            }
        ],
    )
    forward_from_message_id: int | None = Field(
        default=None,
        title="Forwarded From Message ID",
        description="Message ID in the original chat from which the message was forwarded.",
        deprecated=False,
        examples=[156],
    )
