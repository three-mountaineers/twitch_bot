from typing import TypedDict, Optional, Literal

from mountaineer_bot.tw_events.types import base_messages as bm

class AutomodMessageHoldV1(bm.BroadCasterDetails, bm.UserDetails):
    message_id: str
    message: str
    level: int
    category: str
    held_at: str
    fragments: bm.FragmentsV1

class AutomodMessageHoldV2(bm.BroadCasterDetails, bm.UserDetails):
    message_id: str
    message: bm.Message
    reason: Literal['automod','blocked_term']
    automod: Optional[bm.AutoMod]
    blocked_term: Optional[bm.BlockedTerm]
    held_at: str

class AutoModMessageUpdateV1(AutomodMessageHoldV1, bm.ModeratorDetails):
    status: str

class AutoModMessageUpdateV2(AutomodMessageHoldV2, bm.ModeratorDetails):
    status: str

class AutomodSettingsUpdate(bm.BroadCasterDetails, bm.ModeratorDetails):
    bullying: int
    overall_level: Optional[int]
    disability: int
    race_ethnicity_or_religion: int
    misogyny: int
    sexuality_sex_or_gender: int
    aggression: int
    sex_based_terms: int
    swearing: int

class AutomodTermsUpdate(bm.BroadCasterDetails, bm.ModeratorDetails):
    action: str
    from_automd: bool
    terms: list[str]

class ChannelAdBreakBegin(bm.BroadCasterDetails, bm.RequesterUserDetails):
    is_automatic: bool
    started_at: str
    duration_seconds: int

class ChannelBan(bm.UserDetails, bm.ModeratorDetails, bm.BroadCasterDetails):
    reason: str
    banned_at: str
    ends_at: str
    is_permanent: str

class ChannelChatClear(bm.BroadCasterDetails):
    pass

class ChannelChatMessage(bm.BroadCasterDetails, bm.ChatterUserDetails):
    message_id: str
    message: bm.Message
    message_type: Literal['text','channel_points_highlighted','channel_points_sub_only','user_intro','power-ups_message_effect','power_ups_gigantified_emote']
    badges: list[bm.Badge]
    cheer: Optional[bm.Cheer]
    color: str
    reply: Optional[bm.Reply]
    channel_points_custom_reward_id: Optional[str]
    source_broadcaster_user_id: Optional[str]
    source_broadcaster_user_name: Optional[str]
    source_broadcaster_user_login: Optional[str]
    source_message_id: Optional[str]
    source_badges: Optional[list[bm.Badge]]

class ChannelChatMessageDelete(bm.BroadCasterDetails, bm.TargetUserDetails):
    message_id: str

class ChannelChatNotification(bm.BroadCasterDetails):
    chatter_user_id: str
    chatter_user_name: str
    chatter_is_anonymous: bool
    color: str
    badges: list[bm.Badge]
    system_message: str
    message_id: str
    message: bm.Message
    notice_type: Literal[
        'sub',
        'resub',
        'sub_gift',
        'community_sub_gift',
        'gift_paid_upgrade',
        'prime_paid_upgrade',
        'raid',
        'unraid',
        'pay_it_forward',
        'annoucement',
        'bit_badge_tier',
        'charity_donation',
        'shared_chat_sub',
        'shared_chat_resub',
        'shared_chat_sub_gift',
        'shared_chat_community_sub_gift',
        'shared_chat_gift_paid_upgrade',
        'shared_chat_prime_paid_upgrade',
        'shared_chat_raid',
        'shared_chat_pay_it_forward',
        'shared_chat_announcement',
    ]
    sub: bm.Sub
    resub: bm.ReSub
    sub_gift: bm.SubGift
    community_sub_gift: bm.CommunityGift
    gift_paid_upgrade: bm.GifterDetails
    prime_paid_upgrade: bm.PrimePaidUpgrade
    pay_it_forward: bm.PayItForward
    raid: bm.Raid
    unraid: Optional[dict]
    annoucement: Optional[bm.Announcement]
    bits_badge_tier: Optional[bm.BitsBadgeTier]
    charity_donation: Optional[bm.CharityDonation]
    source_broadcaster_user_id: Optional[str]
    source_broadcaster_user_name: Optional[str]
    source_broadcaster_user_login: Optional[str]
    source_message_id: Optional[str]
    source_badges: Optional[list[bm.Badge]]
    shared_chat_sub: Optional[bm.Sub]
    shared_chat_resub: Optional[bm.ReSub]
    shared_chat_sub_gift: Optional[bm.SubGift]
    shared_chat_community_sub_gift: Optional[bm.CommunityGift]
    shared_chat_gift_paid_upgrade: Optional[bm.GifterDetails]
    shared_chat_prime_paid_upgrade: Optional[bm.PrimePaidUpgrade]
    shared_chat_pay_it_forward: Optional[bm.PayItForward]
    shared_chat_raid: Optional[bm.Raid]
    shared_chat_announcement: Optional[bm.Announcement]

class ChannelChatSettingsUpdate(bm.BroadCasterDetails):
    emote_mode: bool
    follower_mode: bool
    follower_mode_duration_minutes: int
    slow_mode: int
    slow_mode: bool
    slow_mode_wait_time_seconds: int
    subscriber_mode: bool
    unique_chat_mode: bool

class ChannelChatUserMessageHold(bm.BroadCasterDetails, bm.UserDetails):
    message_id: str
    message: list[bm.Message]

class ChannelChatUserMessageUpdate(ChannelChatUserMessageHold):
    status: Literal['approved','denied','invalid']

class ChannelSubscibe(bm.BroadCasterDetails, bm.UserDetails):
    tier: bm.SubTier
    is_gift: bool

class ChannelCheer(bm.BroadCasterDetails, bm.UserDetails):
    message: str
    is_anonymous: bool
    bits: int

class ChannelUpdate(bm.BroadCasterDetails):
    title: str
    language: str
    category_id: str
    category_name: str
    content_classification_labels: list[str]

class ChannelUnban(bm.BroadCasterDetails, bm.UserDetails, bm.ModeratorDetails):
    pass

class ChannelUnbanRequestCreate(bm.BroadCasterDetails, bm.UserDetails):
    id: str
    text: str
    created_at: str

class ChannelUnbanRequestResolve(bm.BroadCasterDetails, bm.UserDetails):
    id: str
    resolution_text: str
    status: Literal['approved','canceled','denied']

class ChannelFollow(bm.UserDetails, bm.BroadCasterDetails):
    followed_at: str

class ChannelRaid(TypedDict):
    from_broadcaster_user_id: str
    from_broadcaster_user_name: str
    from_broadcaster_user_login: str
    to_broadcaster_user_id: str
    to_broadcaster_user_name: str
    to_broadcaster_user_login: str
    viewers: int

class StreamOnline(bm.BroadCasterDetails):
    id: str
    type: Literal['live','playlist','watch_party','premiere','rerun']
    started_at: str

class StreamOffline(bm.BroadCasterDetails):
    pass

class GoalsBegin(bm.BroadCasterDetails):
    id: str
    type: Literal['follow','subscription','subscription_count','new_subscription','new_subscription_count','new_bit','new_cheerer']
    description: str
    current_amount: int
    target_amount: int
    started_at: str
    
class GoalsEnd(GoalsBegin):
    is_achieved: bool
    ended_at: str