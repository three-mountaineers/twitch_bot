from typing import TypedDict, NotRequired, Optional, Literal

EmotesV1 = TypedDict(
    'Emotes', 
    {
        "text": str,
        "id": str,
        "set-id": str
    }
)

class EmotesV2(TypedDict):
    id: str
    emote_set_id: str
    owner_id: NotRequired[str]
    format: NotRequired[list[str]]

class CheerMotes(TypedDict):
    text: NotRequired[str]
    amount: NotRequired[int]
    prefix: str
    tier: int
    bits: NotRequired[int]

class FragmentsV1(TypedDict):
    emotes: list[EmotesV1]
    cheermotes: list[CheerMotes]

class FragmentsV2(TypedDict):
    type: Literal['text','cheermote','emote','mention']
    text: str
    emotes: Optional[EmotesV2]
    cheermotes: Optional[CheerMotes]

class BroadCasterDetails(TypedDict):
    broadcaster_user_id: str
    broadcaster_user_name: str
    broadcaster_user_login: str

class ModeratorDetails(TypedDict):
    moderator_user_id: str
    moderator_user_login: str
    moderator_user_name: str

class UserDetails(TypedDict):
    user_id: str
    user_name: str
    user_login: str

class OwnerBroadCasterDetails(TypedDict):
    owner_broadcaster_user_id: str
    owner_broadcaster_user_name: str
    owner_broadcaster_user_login: str

class RequesterUserDetails(TypedDict):
    requester_user_id: str
    requester_user_name: str
    requester_user_login: str

class TargetUserDetails(TypedDict):
    target_user_id: str
    target_user_name: str
    target_user_login: str

class ChatterUserDetails(TypedDict):
    chatter_user_id: str
    chatter_user_name: str
    chatter_user_login: str

class Message(TypedDict):
    text: str
    fragments: list[FragmentsV2]
    mention: NotRequired[Optional[UserDetails]]

class Badge(TypedDict):
    set_id: str
    id: str
    info: str

class Cheer(TypedDict):
    bits: int

class Reply(TypedDict):
    parent_message_id: str
    parent_message_body: str
    parent_user_id: str
    parent_user_name: str
    parent_user_login: str
    thread_message_id: str
    thread_user_id: str
    thread_user_name: str
    thread_user_login: str

class Boundary(TypedDict):
    start_pos: int
    end_pos: int

class Terms(OwnerBroadCasterDetails):
    term_id: str
    boundary: Boundary

class AutoMod(TypedDict):
    category: str
    level: int
    boundaries: list[Boundary]

class BlockedTerm(TypedDict):
    terms_found: list[Terms]

SubTier = Literal['1000','2000','3000']

class Sub(TypedDict):
    sub_tier: SubTier
    is_prime: bool
    duration_months: int

class GifterDetails(TypedDict):
    gifter_user_id: Optional[str]
    gifter_user_name: Optional[str]
    gifter_user_login: Optional[str]

class ReSub(Sub, GifterDetails):
    cumulative_months: int
    streak_months: int
    is_gift: bool
    gifter_is_anonymous: Optional[bool]

class SubGift(Sub):
    cumulative_total: Optional[int]
    recipient_user_id: str
    recipient_user_name: str
    recipient_user_login: str
    community_gift_id: Optional[str]

class CommunityGift(Sub):
    id: str

class PrimePaidUpgrade(TypedDict):
    sub_tier: SubTier

class PayItForward(GifterDetails):
    gifter_is_anonymous: bool

class Raid(UserDetails):
    viewer_count: int
    profile_image_url: str

class Announcement(TypedDict):
    color: str

class BitsBadgeTier(TypedDict):
    tier: int

class Amount(TypedDict):
    value: int
    decimal_place: int
    currency: str

class CharityDonation(TypedDict):
    charity_name: str
    amount: Amount
