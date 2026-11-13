-- Logs every change of the task slots (3 groups x 6 slots at 0x8010CBB0, runner 8002EFB4) and of STAGE NO /
-- DIFFICULT (debug print 8007F920). Recon probe: emu.py ... --script tools/debug/tasklog.lua
local mem = PCSX.getMemPtr()
local function r16(a) a = a % 0x200000; return mem[a] + mem[a + 1] * 256 end
local function r32(a) return r16(a) + r16(a + 2) * 65536 end
local last = {}
local WATCH = WATCH or {}
L.on_frame(function()
  local parts = {}
  for g = 0, 2 do
    for i = 0, 5 do
      local b = 0x10CBB0 + g * 0xF4 + 4 + i * 0x28
      parts[#parts + 1] = string.format("%d.%d=%08X", g, i, r32(b + 4))
    end
  end
  parts[#parts + 1] = string.format("stage=%d diff=%d", r32(0x0CBE7C), r32(0x0CBF88))
  local t = {}
  for o = 0x10CBB0 + 8, 0x10CBB0 + 0x2C, 2 do t[#t + 1] = string.format("%04X", r16(o)) end
  parts[#parts + 1] = "s0=" .. table.concat(t, ".")
  for _, a in ipairs(WATCH) do parts[#parts + 1] = string.format("%X=%X", a, r16(a)) end
  local s = table.concat(parts, " ")
  if s ~= last.s then L.log(string.format("%d %s", L.frame, s)); last.s = s end
end)
