# Discord trial setup and live evidence

Use only the empty **HandoffReady Trial** server. The tester must use their own Discord account/device. Start with synthetic files.

The installed Switch Console 0.40.1 supports Discord. Its bridge connects outward; exposing the local review desk publicly is unnecessary. Follow the [official version-specific setup](https://github.com/sandbox-quantum/switch/blob/switch-console-v0.40.1/docs/old/bridges/DISCORD_SETUP.md).

## Reproduce the owner setup

The account owner creates a bot in the [Discord Developer Portal](https://discord.com/developers/applications), handles any terms, and approves its invitation into the test server. Follow the official guide for required intents and named permissions. Do not give it Administrator or invite it to unrelated servers. Yash completed these account actions for application `1567477402534158406`; do not repeat them.

Switch's operator dashboard registers the Discord messaging app using the bot token and server ID. Enter credentials directly in that setup UI; keep the token out of chat, source files and screenshots. A successful invitation alone does not prove a working bridge. Fresh native Console inspection showed **Messaging apps: 1**, named **HandoffReady Trial**. No token was read or copied into project files.

## Room and actual message route verified

Yash created the synthetic-only handoffready-delivery room with switch-buddy-admin. A real read-only agent diagnostic reported Switch room ID `24b45a9e-0542-4e98-9338-1945a79a832f`, Discord channel ID `1567485560983912452`, active connection and live membership. These values were initially agent-reported.

Independent native Discord inspection subsequently confirmed the channel, topic, bot greeting, Yash's addressed diagnostic at approximately **4:04 PM IST on 4 November**, and the actual response **ROOM_READY — I received your message.** [Trial channel](https://discord.com/channels/1567472576207528028/1567485560983912452). This verifies a real owner-to-agent-to-Discord message route. It is not a second-person test or completed delivery review.

## Attachment round trip independently verified

Yash uploaded `HandoffReady-probe-20261104.txt` and sent an addressed instruction. The agent returned a native attachment named `9d5ed198f57c48719d9453e1ac3f777c-HandoffReady-probe-20261104.txt`. Computer control could open its download menu but could not activate Download, so Yash downloaded it himself.

The downloaded return was independently read and compared with the original, rather than relying on the model's reported hash. **All 109 bytes are equal.** Both SHA-256 values are `b084027bd24430e099ed2b55db7c916379e10110b7b2677c6ea2ab3ffc9fb75f`. The receipt at `execution/discord-roundtrip-receipt.json`, outside the repository, records verification at **10:47:09 UTC / 4:17:09 PM IST on 4 November 2026**. This is an owner-operated synthetic file test, not a colleague trial or completed business workflow.

## Project service and dedicated agent

The isolated local review service runs at http://127.0.0.1:8896 with disposable data under `execution/private/app-data`, bound to the verified room. An empty synthetic project and delivery job exist; direct stdio-to-service status returned `scope_review`. No human assessment was saved.

Native Console now shows **handoffready-yash · Codex** created and running. Its workspace has project-scoped configuration for only `delivery_status` and `delivery_check_preview`, using a private client configuration file outside Git. No global MCP configuration was manually changed. The earlier separate CODEX_HOME prototype is inactive; its private authentication-file reference reuses existing authorized login without reading or printing credential contents. Neither prototype preparation nor agent creation proves that Switch loaded the custom tools.

Actual custom MCP invocation inside the Switch-managed agent is **not yet verified**. The dedicated agent is **not yet verified as a delivery-room member**. These application tool restrictions are not OS isolation against a same-user assistant with other tools.

## Remaining gates

1. Observe an actual custom tool invocation by handoffready-yash and verify its delivery-room membership.
2. Configure and verify second-person permissions using their own account/device.
3. Complete explicit packet intake, meaningful clarification, correction and fresh human review through that room.
4. Preview an intentionally shared frozen record, return its real artifact and reconcile an uncertain send honestly.
5. Complete a genuine colleague trial, second packet and offline/reconnect rehearsal. Never present the owner smoke test as those results.

## Recovery and working scoped status bridge

The user accidentally deleted the dedicated Codex delivery agent. Its project job, workspace instructions and the existing Discord room remained intact. Recreated handoffready-yash with Antigravity, bypass off, management off and existing owner-only addressing. A real Console TOOL_SPIKE executed the approved private-config delivery_status CLI and returned scope_review with the local human reviewer as next actor. This is a command-tool bridge, not native custom MCP.

The user sent Switch’s documented !invite-agent command in the existing channel. Discord displayed the restored agent greeting; Console independently shows2agents/1person, naming switch-buddy-admin and handoffready-yash. No new room, packet or formal human assessment was created. This verifies recovery and membership; the dedicated-agent room file/correction loop and second-person trial remain open.
