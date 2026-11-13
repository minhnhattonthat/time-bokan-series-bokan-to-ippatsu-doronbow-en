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
  W.frames(150)
  W.shot("card")
  if card_only then return end
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
  W.frames(200)
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

S.memcard = function()
  to_menu()
  W.tap("down"); W.frames(30); W.tap("down"); W.frames(30)
  W.tap("circle")
  W.wait_sub(W.MEMCARD, 0xB, 900)
  W.frames(60)
  W.shot("menu")
  W.tap("circle")
  for i = 1, 6 do W.frames(60); W.shot(string.format("save%d", i)) end
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
    L.dump_ram(string.format("%s/ram_%02d.bin", DIR, i))
    L.log(string.format("ram %d scroll=%d task=%08X", i, math.floor(W.r32(0x1490FC) / 65536), W.task()))
  end
  W.done()
end

S.x_tour = function()
  to_stage(TRY or 1)
  GOD = 1
  L.press("circle", 40000)
  for i = 1, (NSHOTS or 40) do
    W.frames(STEP or 600)
    W.shot(string.format("t%03d_%08X_%d_%d", i, W.task(), math.floor(W.r32(W.SCROLL) / 65536), W.r8(W.SHIELD1)))
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
  end
  local i = 0
  for b in SEQ:gmatch("[^ ]+") do
    i = i + 1
    if b:sub(1, 2) == "p2" then W.tap2(b:sub(4)) elseif b ~= "-" then W.tap(b) end
    W.frames(WAIT or 50)
    W.shot(string.format("s%02d_%s_%08X_%X_%X_%X_%X", i, b, W.task(), W.sub(), W.r32(0xD7C70), W.r32(0xD7C74),
      W.r32(0xD7C80)))
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
