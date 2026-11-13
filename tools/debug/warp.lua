-- Cold-boot warp: plays each scene in tools/debug/scenes.lua as a coroutine that waits on game state, never on frame
-- counts it hopes are right. Addresses and task functions: docs/re/state.md.
-- Use: emu.py CUE --out D --frames 40000 --timeout 900 --script tools/debug/warp.lua --script tools/debug/scenes.lua
--      --var "SCENE='title'"; optional: --var GOD=1 pins the shield. warp_all.py runs the whole list.
local mem = PCSX.getMemPtr()
-- Opt-in hardware: P2=1 plugs in pad 2 (off in PCSX-Redux by default, so W.tap2 did nothing); NOCARD=1 pulls card 1.
if P2 then PCSX.settings.pads[2].Connected = true end
if NOCARD then PCSX.settings.emulator.Mcd1Inserted = false end
W = {}
function W.r8(a) return mem[a % 0x200000] end
function W.r16(a) a = a % 0x200000; return mem[a] + mem[a + 1] * 256 end
function W.r32(a) return W.r16(a) + W.r16(a + 2) * 65536 end
function W.w8(a, v) mem[a % 0x200000] = v % 256 end
function W.w16(a, v) a = a % 0x200000; mem[a] = v % 256; mem[a + 1] = math.floor(v / 256) % 256 end
function W.w32(a, v) W.w16(a, v % 65536); W.w16(a + 2, math.floor(v / 65536) % 65536) end

-- Game state (docs/re/state.md). The main task is slot 0 of task group 0 (runner 8002EFB4): its function says which
-- screen runs, its +8 word is that screen's sub-state.
W.TASK = 0x10CBB8  -- u32 function of the main task
W.SUB = 0x10CBBC   -- u32 its sub-state
W.STAGE = 0x0CBE7C -- u32 stage number 1-7 (debug print "STAGE NO")
W.DIFF = 0x0CBF88  -- u32 difficulty (debug print "DIFFICULT")
W.CUR = 0x0D7C70   -- u32 title menu cursor: 0 start, 1 options, 2 memory card
W.FLAGS = 0x0D7C64 -- u32 title event bits: 0x40000000 press-start shown, 0x00F00000 menu open

-- Main task functions
W.LOGO = 0x80016F1C
W.TITLE = 0x8001751C
W.MOVIE = 0x80019D20
W.SELECT = 0x80020C4C
W.CARD = 0x80027850
W.STAGE_TASK = 0x8002DDFC
W.DEMO = 0x8002E28C
W.OPTIONS = 0x8001A0D8
W.MEMCARD = 0x8001D50C
W.GAMEOVER = 0x8002BBB0
W.RANKING = 0x800286BC
W.ENDING = 0x80031020

-- Task slots: group g slot i at 0x8010CBB4 + g*0xF4 + i*0x28: +0 u16 delay, +2 u16, +4 function, +8 state, +0xC arg.
W.SLOTS = 0x10CBB4
-- W.call(fn, a0): runs the game function fn(a0) once from task context, the way a stage object calls it (a stage
-- clear calls 80021918 or 80019CB8). It writes a stub into the unused debug-print strings (EXE 0x2D30, read only by
-- the never-called debug print 8007F058) and starts it in a free slot of group 0; the stub kills its own slot and
-- tail-jumps to fn, so fn returns into the task runner. Each call takes a fresh stub (the recompiler caches code).
local stub_n = 0
function W.call(fn, a0)
  local stub = 0x80012530 + stub_n * 0x20
  stub_n = stub_n + 1
  assert(stub_n <= 8, "out of stub space")
  local code = {
    0x3C08800D,                       -- lui  t0, 0x800d
    0x8D08BD80,                       -- lw   t0, -0x4280(t0)   current slot
    0x00000000,
    0xAD000004,                       -- sw   zero, 4(t0)       kill this slot
    0x3C040000 + math.floor(a0 / 65536) % 65536, -- lui a0, hi
    0x34840000 + a0 % 65536,          -- ori  a0, a0, lo
    0x08000000 + math.floor(fn / 4) % 0x4000000, -- j fn
    0x00000000,
  }
  for i, w in ipairs(code) do W.w32(stub + (i - 1) * 4, w) end
  for i = 0, 5 do
    local s = W.SLOTS + i * 0x28
    if W.r32(s + 4) == 0 then
      W.w32(s + 8, 0); W.w32(s + 0xC, 0); W.w32(s, 0)
      W.w32(s + 4, stub)
      L.log(string.format("%d call %08X(%X) from slot 0.%d", L.frame, fn, a0, i))
      return
    end
  end
  error("no free task slot in group 0")
end

W.SHIELD1 = 0x0D421D -- u8 3 at start, falls with hits: a HUD copy, not what the death check reads
-- Player structs at 0x800D7D28, stride 0x80: +0 CND, +2 ACTCND (4 = dying), +0x24 s32 HP, 0x2000 full; the hit code
-- 80046AC0 kills the player when HP <= 0. GOD pins it full for both players.
W.HP1 = 0x0D7D4C
W.SCROLL = 0x1490FC  -- s32 scroll Y, 16.16 (debug print "SCROLL Y"); counts down, holds still at mid-bosses
function W.god()
  if W.task() == W.STAGE_TASK then W.w32(W.HP1, 0x2000); W.w32(W.HP1 + 0x80, 0x2000) end
end

function W.task() return W.r32(W.TASK) end
function W.sub() return W.r32(W.SUB) end

local checks = {}
function W.frames(n) for _ = 1, n do coroutine.yield() end end
-- Fails the run (exit 2) if the game never reaches the state: a wrong warp must not pass as a shot of something else.
function W.wait(cond, what, limit)
  limit = limit or 6000
  local n = 0
  while not cond() do
    n = n + 1
    if n > limit then
      error(string.format("warp timeout waiting for %s task=%08X sub=%X", tostring(what), W.task(), W.sub()))
    end
    coroutine.yield()
  end
  L.log(string.format("%d reached %s", L.frame, tostring(what)))
end
function W.wait_task(fn, limit)
  W.wait(function() return W.task() == fn end, string.format("task %08X", fn), limit)
end
function W.wait_sub(fn, s, limit)
  W.wait(function() return W.task() == fn and W.sub() == s end, string.format("task %08X sub %X", fn, s), limit)
end
function W.tap(btn, hold) L.press(btn, hold or 6); L.press("-", 2); W.frames((hold or 6) + 2) end
-- Pad 2 (emu.py drives pad 1 only): hold one button for `hold` frames.
function W.tap2(btn, hold)
  local b = PCSX.CONSTS.PAD.BUTTON[btn:upper()]
  local pad2 = PCSX.SIO0.slots[2].pads[1]
  pad2.setOverride(b); W.frames(hold or 6); pad2.clearOverride(b); W.frames(2)
end
function W.shot(name) L.shot(name .. ".png"); L.log(string.format("%d shot %s", L.frame, name)) end
function W.check(ok, what)
  checks[#checks + 1] = what
  if not ok then error("check failed: " .. what) end
  L.log("check ok: " .. what)
end
function W.done()
  L.shot("final.png")
  L.log(string.format("warp done %s frame %d", SCENE, L.frame))
  if STATE_OUT then L.save_state(STATE_OUT) end
  L.finish(0)
  while true do coroutine.yield() end
end

local co
L.on_frame(function()
  if not co then
    if not SCENES then error("load tools/debug/scenes.lua with --script") end
    local fn = SCENES[SCENE]
    if not fn then error("unknown scene " .. tostring(SCENE)) end
    co = coroutine.create(fn)
  end
  if GOD and W.god then W.god() end
  local ok, e = coroutine.resume(co)
  if not ok then error(e) end
end)
