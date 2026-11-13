-- Load after warp.lua and scenes.lua: every W.shot and W.done also writes <name>.ram.bin and <name>.vram.bin, which
-- tools/prims.py reads for the GPU primitives of that frame.
local shot, done = W.shot, W.done
function W.shot(name)
  L.dump_ram(name .. ".ram.bin")
  L.dump_ppu(name)
  shot(name)
end
function W.done()
  L.dump_ram("final.ram.bin")
  L.dump_ppu("final")
  done()
end
