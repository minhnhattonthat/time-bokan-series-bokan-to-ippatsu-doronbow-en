-- Scene list for warp.lua: name -> function run as a coroutine from cold boot. See docs/re/state.md.
SCENES = {}
local S = SCENES

-- Start ends a movie once it plays; the movie task ignores it while the stream starts, so tap until it leaves.
local function skip_movie()
  W.wait_task(W.MOVIE, 4000)
  for _ = 1, 40 do
    if W.task() ~= W.MOVIE then return end
    W.tap("start"); W.frames(22)
  end
  error("movie did not end on Start")
end

-- Logo task 80016F1C hands over to the movie task (opening MOVE01), then the title.
local function to_title()
  skip_movie()
  W.wait_sub(W.TITLE, 0xA, 1200)
  W.wait(function() return W.r32(W.FLAGS) & 0x40000000 ~= 0 end, "press start shown", 900)
  W.frames(30)
end

local function to_menu()
  to_title()
  W.tap("start")
  W.wait_sub(W.TITLE, 0xB, 600)
  W.frames(40)
end

-- Menu row 0: start. The game plays MOVE02 (Start skips it), then ship select.
local function to_select()
  to_menu()
  W.check(W.r32(W.CUR) == 0, "menu cursor on start")
  W.tap("circle")
  skip_movie()
  W.wait_task(W.SELECT, 1200)
end

-- Ship select with the stage number set: the select's card and stage load follow it. Circle takes the ship under the
-- cursor; `ship` moves right that many times first.
local function to_stage(n, ship, card_only)
  to_select()
  W.wait_sub(W.SELECT, 0x13, 1200)
  W.frames(60)
  W.w32(W.STAGE, n)
  for _ = 1, ship or 0 do W.tap("right"); W.frames(20) end
  W.tap("circle")
  W.wait_task(W.CARD, 2000)
  if card_only then  -- the title zooms and flips in and out: a burst of shots catches it whole
    for i = 1, 16 do W.frames(30); W.shot(string.format("card%02d", i)) end
    return
  end
  W.frames(150)
  W.shot("card")
  W.wait_task(W.STAGE_TASK, 2000)
  W.frames(120)
end

-- What each stage's clear object does when its boss dies (BOKAN<n>.BIN, docs/re/state.md).
local function clear(n)
  if n == 3 then
    W.w32(W.STAGE, 4); W.w8(0x0CBF70, 0xFF); W.call(0x80019CB8, 2) -- MOVE03, then ship select
  elseif n == 7 then
    W.call(0x80019CB8, 3)                                         -- MOVE04, MOVE05, ending
  else
    W.w32(W.STAGE, n + 1); W.call(0x80021918, 0)                  -- ship select for the next stage
  end
end

S.title = function()
  to_title()
  W.done()
end

S.menu = function()
  to_menu()
  W.shot("start")
  W.tap("down"); W.frames(30); W.shot("options")
  W.tap("down"); W.frames(30); W.shot("card")
  W.check(W.r32(W.CUR) == 2, "menu cursor on memory card")
  W.done()
end

S.logo = function()
  W.wait_task(W.LOGO, 3000)
  W.frames(200)
  W.check(W.task() == W.LOGO, "logo task")
  W.done()
end

S.movie01 = function()
  W.wait_task(W.MOVIE, 3000)
  W.frames(600)
  W.check(W.task() == W.MOVIE, "opening movie playing")
  W.done()
end

S.movie02 = function()
  to_menu()
  W.tap("circle")
  W.wait_task(W.MOVIE, 600)
  W.frames(900)
  W.check(W.task() == W.MOVIE, "game-start movie playing")
  W.done()
end

-- Title left alone: the 900-frame idle starts the attract demo (stages 1-3), then the attract ranking.
S.demo = function()
  to_title()
  W.wait_task(W.DEMO, 2400)
  W.frames(900)
  W.done()
end

S.ranking = function()
  to_title()
  W.wait_task(W.RANKING, 12000)
  for i = 1, 12 do W.frames(60); W.shot(string.format("rank%02d", i)) end -- the table builds in after the backdrop
  W.done()
end

S.options = function()
  to_menu()
  W.tap("down"); W.frames(30); W.tap("circle")
  W.wait_sub(W.OPTIONS, 0x14, 900)
  W.frames(60)
  for i = 1, 7 do
    W.shot(string.format("row%d", W.r32(W.CUR)))
    W.tap("down"); W.frames(40)
  end
  W.done()
end

-- Sound test: every value of the sound row (0x800D7C74), one shot each.
S.sound = function()
  to_menu()
  W.tap("down"); W.frames(30); W.tap("circle")
  W.wait_sub(W.OPTIONS, 0x14, 900)
  W.frames(60)
  W.tap("down"); W.frames(40); W.tap("down"); W.frames(40)
  W.check(W.r32(W.CUR) == 3, "options cursor on sound test")
  for _ = 0, 0x32 do
    W.shot(string.format("snd%02X", W.r32(0x0D7C74)))
    W.tap("right"); W.frames(30)
  end
  W.done()
end

-- Memory card screen (menu sub-state 0xB). warp_all.py gives each scene its card (tools/mcd.py, `CARDS` there).
local function to_card()
  to_menu()
  W.tap("down"); W.frames(30); W.tap("down"); W.frames(30)
  W.tap("circle")
  W.wait_sub(W.MEMCARD, 0xB, 900)
  W.frames(150) -- the menu ignores circle until it settles
  W.shot("menu")
end
-- Circle on the row under the cursor, then a shot every 30 frames until the menu is back (or `n` shots).
local function card_do(tag, n)
  W.tap("circle")
  for i = 1, n or 8 do W.frames(30); W.shot(string.format("%s%d", tag, i)) end
  W.check(W.task() == W.MEMCARD, "memory card screen")
end

-- Options: each value of each row (level, credit, shot key, bomb key), right-stepped with a shot per value.
S.optvals = function()
  to_menu()
  W.tap("down"); W.frames(30); W.tap("circle")
  W.wait_sub(W.OPTIONS, 0x14, 900)
  W.frames(60)
  for _ = 1, 5 do -- rows 1, 2, 3, 5, 6 (down skips 4)
    local row = W.r32(W.CUR)
    if row ~= 3 then
      for v = 1, 6 do W.shot(string.format("row%d_v%d", row, v)); W.tap("right"); W.frames(40) end
    end
    W.tap("down"); W.frames(40)
  end
  W.check(W.r32(W.CUR) == 7, "options cursor on EXIT")
  W.done()
end

-- Continue: holding cross (the bomb) leaves the ship open to one-hit kills (TYPE INF1 800D7D2E = 1), so it dies
-- fast; with no ship left (PLY NUM 800CBDE4 = 0) the stage shows CONTINUE? and a countdown. Start takes it.
S.continue = function()
  to_stage(1)
  local out = function() return W.r16(0x0CBDE4) == 0 and W.r8(0x0D7D2A) == 4 end
  -- L.press queues (pcsx_lib), so a long hold would delay every later press: hold in 10-frame chunks
  for _ = 1, 900 do
    if out() then break end
    L.press("cross", 10); W.frames(10)
  end
  W.wait(out, "1P out of ships", 60)
  for i = 1, 4 do W.frames(60); W.shot(string.format("cont%d", i)) end
  W.check(W.task() == W.STAGE_TASK and W.r8(0x0CBE98) > 0, "continue prompt with credits")
  local credits = W.r8(0x0CBE98)
  W.tap("start") -- the prompt reads Start (0x800) from the stage's pad edge 0x800CBF30
  W.wait(function() return W.r8(0x0CBE98) == credits - 1 end, "credit used", 120)
  for i = 1, 10 do W.frames(60); W.shot(string.format("after%d", i)) end
  W.done()
end

-- 2P joins at ship select (needs P2=1: warp_all.py sets it). Start on pad 2, then each pad picks.
S.join2p = function()
  to_select()
  W.wait_sub(W.SELECT, 0x13, 1200)
  W.frames(60)
  W.shot("alone")
  W.tap2("start"); W.frames(60); W.shot("p2_start")
  W.tap2("right"); W.frames(40); W.shot("p2_right")
  W.tap2("circle"); W.frames(60); W.shot("p2_ok")
  W.tap("circle"); W.frames(60); W.shot("p1_ok")
  W.wait_task(W.CARD, 2000)
  W.frames(150); W.shot("card")
  W.wait_task(W.STAGE_TASK, 2000)
  W.frames(300)
  W.done()
end

S.memcard = function() to_card(); card_do("save"); W.done() end            -- blank card: アクセス中, セーブOK!
S.memcard_load = function()                                                 -- blank card: データがありません
  to_card(); W.tap("down"); W.frames(40); card_do("load"); W.done()
end
S.memcard_loadok = function()                                               -- save, then load it back: ロードOK!
  to_card(); card_do("save", 6); W.wait_sub(W.MEMCARD, 0xB, 900); W.frames(60)
  W.tap("down"); W.frames(40); card_do("load"); W.done()
end
S.memcard_full = function() to_card(); card_do("save"); W.done() end       -- full card: 空き容量が足りません
S.memcard_nocard = function()                                               -- no card: カードが差されてません
  to_card(); card_do("save"); W.tap("down"); W.frames(40); card_do("load"); W.done()
end
S.memcard_format = function()                                               -- unformatted: format prompt, YES/NO
  to_card()
  card_do("save", 4)                                  -- このメモリーカードは フォーマットされてません
  W.tap("circle"); W.frames(40); W.shot("ask")        -- フォーマットしますか? YES NO (0x800D7C74 = 1: NO)
  W.tap("right"); W.frames(40); W.shot("ask_yes")     -- 0x800D7C74 = 0
  W.check(W.r32(0x0D7C74) == 0, "format answer YES")
  W.tap("circle")
  for i = 1, 6 do W.frames(30); W.shot(string.format("fmt%d", i)) end
  W.done()
end

-- Stage 1 left alone: the ship dies, game over, ranking, back to the title.
S.gameover = function()
  to_stage(1)
  W.wait_task(W.GAMEOVER, 12000)
  for i = 1, 8 do W.frames(60); W.shot(string.format("go%d", i)) end
  W.done()
end

for n = 1, 7 do S["card" .. n] = function() to_stage(n, 0, true); W.done() end end
for n = 1, 7 do S["stage" .. n] = function() to_stage(n); W.frames(600); W.done() end end
-- Clear: the stage's own clear sequence from its first seconds; shots until the next screen settles. clear3 shows
-- MOVE03; clear7 rolls MOVE04, MOVE05, the ending and staff roll, MOVE06 and the end-of-game screen.
for n = 1, 7 do S["clear" .. n] = function()
  to_stage(n)
  clear(n)
  local limit = n == 7 and 110 or 30
  for i = 1, limit do
    W.frames(300)
    W.shot(string.format("c%03d", i))
    if n ~= 7 and i > 2 and W.task() == W.SELECT then break end
    if n == 7 and W.task() == W.GAMEOVER then break end
  end
  W.check(W.task() == (n == 7 and W.GAMEOVER or W.SELECT), "next screen after clear")
  W.frames(300)
  W.done()
end end
-- Staff roll for tools/credits.py: MOVE05 then the ending, a shot every STEP frames (default 60) while the ending runs.
-- With --prims each shot carries the quads on screen, which give each credit line's pieces.
S.staff = function()
  to_stage(7)
  W.call(0x80019CB8, 4)                                           -- MOVE05, then the ending
  W.wait_task(W.ENDING, 9000)
  local i = 0
  while W.task() == W.ENDING do
    W.frames(STEP or 60)
    i = i + 1
    W.shot(string.format("s%03d", i))
    assert(i < 400, "ending never ended")
  end
  W.check(i > 100, "staff roll ran")
  W.done()
end
-- Whole stage with GOD and circle (the shot) held: a shot every 300 frames through backgrounds and mid-bosses, until
-- the scroll holds for 3600 frames (the boss arena; mid-bosses hold it for under 2000). Then 6 shots of the boss.
for n = 1, 7 do S["tour" .. n] = function()
  to_stage(n)
  GOD = 1
  L.press("circle", 60000)
  local last, still, i = W.r32(W.SCROLL), 0, 0
  while still < 3600 do
    W.frames(300)
    i = i + 1
    W.shot(string.format("t%03d", i))
    W.check(W.task() == W.STAGE_TASK, "still in the stage")
    local s = W.r32(W.SCROLL)
    if s == last then still = still + 300 else still = 0 end
    last = s
    assert(i < 120, "scroll never settled")
  end
  L.log(string.format("boss scroll %d", math.floor(last / 65536)))
  for j = 1, 6 do W.frames(300); W.shot(string.format("boss%d", j)) end
  W.done()
end end
-- Ship select for stage n, entered the way the game does: clear stage n-1.
for n = 1, 7 do S["select" .. n] = function()
  if n == 1 then to_select() else to_stage(n - 1); clear(n - 1) end
  W.wait_sub(W.SELECT, 0x13, 9000)
  W.check(W.r32(W.STAGE) == n, "stage number " .. n)
  W.frames(60)
  for i = 0, 9 do
    W.shot(string.format("ship%d", i))
    W.tap("right"); W.frames(40)
  end
  W.done()
end end

-- Experiments
S.x_clear = function()
  local n = TRY or 1
  to_stage(n)
  W.shot("stage")
  clear(n)
  -- NSHOTS, not SHOTS: emu.py's driver owns that global
  for i = 1, (NSHOTS or 40) do W.frames(STEP or 300); W.shot(string.format("t%03d_%08X_%X", i, W.task(), W.sub())) end
  W.done()
end

S.x_ram = function()
  to_stage(1)
  for i = 1, 16 do
    W.frames(300)
    L.dump_ram(string.format("%sram_%02d.bin", OUT, i))
    L.log(string.format("ram %d scroll=%d task=%08X", i, math.floor(W.r32(0x1490FC) / 65536), W.task()))
  end
  W.done()
end

S.x_tour = function()
  to_stage(TRY or 1)
  GOD = 1
  L.press(BTN or "circle", 40000)
  for i = 1, (NSHOTS or 40) do
    W.frames(STEP or 600)
    W.shot(string.format("t%03d_%08X_%d_%d", i, W.task(), math.floor(W.r32(W.SCROLL) / 65536), W.r32(W.HP1)))
    if W.task() ~= W.STAGE_TASK then break end
  end
  W.done()
end

-- Log the 1P struct (CND, CNDO, ACTCND, TYPE, HP) and PLY NUM every 10 frames while holding BTN.
S.x_ply = function()
  to_stage(TRY or 1)
  L.press(BTN or "cross", 40000)
  for _ = 1, (NSHOTS or 300) do
    W.frames(10)
    L.log(string.format("ply %d cnd=%d,%d,%d,%d type=%d hp=%d num=%d task=%08X", L.frame, W.r8(0x0D7D28),
      W.r8(0x0D7D29), W.r8(0x0D7D2A), W.r8(0x0D7D2B), W.r8(0x0D7D2E), W.r32(W.HP1), W.r16(0x0CBDE4), W.task()))
    if W.task() ~= W.STAGE_TASK then break end
  end
  W.done()
end

S.x_die = function()
  to_select()
  W.wait_sub(W.SELECT, 0x13, 1200)
  W.frames(60)
  W.tap("circle")
  for i = 1, 60 do W.frames(300); W.shot(string.format("t%02d_%08X_%X", i, W.task(), W.sub())) end
  W.done()
end

S.x_options = function()
  to_menu()
  W.tap("down"); W.frames(30)
  W.tap("circle")
  for i, b in ipairs({ "-", "-", "down", "down", "down", "down", "down", "down", "circle", "-", "cross", "-" }) do
    if b ~= "-" then W.tap(b) end
    W.frames(60)
    W.shot(string.format("s%02d_%s_%08X_%X", i, b, W.task(), W.sub()))
  end
  W.done()
end

S.x_seq = function()
  if START == "opt" then
    to_menu(); W.tap("down"); W.frames(30); W.tap("circle"); W.wait_task(W.OPTIONS, 600); W.frames(150)
  elseif START == "card" then
    to_menu(); W.tap("down"); W.frames(30); W.tap("down"); W.frames(30); W.tap("circle"); W.wait_task(W.MEMCARD, 600)
    W.frames(150)
  elseif START == "select" then
    to_select(); W.wait_sub(W.SELECT, 0x13, 1200); W.frames(60)
  elseif START == "stage" then
    to_stage(TRY or 1)
  end
  local i = 0
  for b in SEQ:gmatch("[^ ]+") do
    i = i + 1
    if b:sub(1, 2) == "p2" then
      local seen = 0
      local pad2 = PCSX.SIO0.slots[2].pads[1]
      local bt = PCSX.CONSTS.PAD.BUTTON[b:sub(4):upper()]
      pad2.setOverride(bt)
      local raw = {}
      for _ = 1, 8 do
        coroutine.yield(); seen = seen | W.r16(0x0CBDB2)
        for _, a in ipairs({ 0x0CBD90, 0x0CBD98, 0x0CBDB0, 0x0CBDB8, 0x0CBDF8 }) do raw[a] = (raw[a] or 0) | W.r32(a) end
      end
      pad2.clearOverride(bt)
      L.log(string.format("p2 %s held bits seen %04X raw %08X %08X %08X %08X %08X", b, seen, raw[0x0CBD90],
        raw[0x0CBD98], raw[0x0CBDB0], raw[0x0CBDB8], raw[0x0CBDF8]))
    elseif b:sub(1, 2) == "w:" then -- w:ADDR=VAL pokes a u32 (hex), e.g. w:D7C70=4
      local a, v = b:match("w:(%x+)=(%x+)")
      W.w32(tonumber(a, 16), tonumber(v, 16))
    elseif b ~= "-" then W.tap(b) end
    W.frames(WAIT or 50)
    W.shot(string.format("s%02d_%s_%08X_%X_%X_%X_%X", i, b, W.task(), W.sub(), W.r32(0xD7C70), W.r32(0xD7C74),
      W.r32(0xD7C80)))
    if DUMP then L.dump_ram(string.format("%sram_s%02d.bin", OUT, i)) end
  end
  W.done()
end

S.x_card = function()
  to_menu()
  W.tap("down"); W.frames(30); W.tap("down"); W.frames(30)
  W.tap("circle")
  for i, b in ipairs({ "-", "-", "down", "circle", "-", "-", "cross", "-", "up", "circle", "-", "-" }) do
    if b ~= "-" then W.tap(b) end
    W.frames(60)
    W.shot(string.format("s%02d_%s_%08X_%X", i, b, W.task(), W.sub()))
  end
  W.done()
end

-- Experiment: stage number written during ship select
S.x_try_stage = function()
  to_select()
  W.wait_sub(W.SELECT, 0x13, 1200)
  W.frames(60)
  W.w32(W.STAGE, TRY or 3)
  W.tap("circle")
  W.wait_task(W.CARD, 2000)
  W.frames(150)
  W.shot("card")
  W.wait(function() return W.task() ~= W.CARD and W.task() ~= 0 end, "stage task", 2000)
  W.frames(200)
  if DUMP then L.dump_ram(DUMP) end
  W.done()
end
