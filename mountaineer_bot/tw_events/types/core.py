from mountaineer_bot.tw_events.types import messages as _mg

AutomodMessageHold = _mg.AutomodMessageHoldV1 | _mg.AutomodMessageHoldV2
AutoModMessageUpdate = _mg.AutoModMessageUpdateV1 | _mg.AutoModMessageUpdateV2
AutomodSettingsUpdate = _mg.AutomodSettingsUpdate
AutomodTermsUpdate =  _mg.AutomodTermsUpdate
ChannelAdBreakBegin = _mg.ChannelAdBreakBegin
ChannelBan = _mg.ChannelBan
ChannelChatClear =  _mg.ChannelChatClear
ChannelChatMessage =_mg.ChannelChatMessage
ChannelChatMessageDelete = _mg.ChannelChatMessageDelete
ChannelChatNotification = _mg.ChannelChatNotification
ChannelChatSettingsUpdate = _mg.ChannelChatSettingsUpdate
ChannelChatUserMessageHold = _mg.ChannelChatUserMessageHold
ChannelChatUserMessageUpdate = _mg.ChannelChatUserMessageUpdate
ChannelSubscibe = _mg.ChannelSubscibe
ChannelCheer = _mg.ChannelCheer
ChannelUpdate = _mg.ChannelUpdate
ChannelUnban = _mg.ChannelUnban
ChannelUnbanRequestCreate = _mg.ChannelUnbanRequestCreate
ChannelUnbanRequestResolve = _mg.ChannelUnbanRequestResolve
ChannelFollow = _mg.ChannelFollow
ChannelRaid = _mg.ChannelRaid
StreamOnline = _mg.StreamOnline
StreamOffline = _mg.StreamOffline
GoalBegin = _mg.GoalsBegin
GoalEnd = _mg.GoalsEnd