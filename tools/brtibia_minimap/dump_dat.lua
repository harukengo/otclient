-- Mod temporario do cliente: exporta cor de minimapa e flags de cada item do Tibia.dat
-- para dump_itens.txt (na pasta de configuracoes do cliente). Uso: ver LEIAME.txt
function init()
  scheduleEvent(function()
    g_game.setClientVersion(860)
    g_game.setProtocolVersion(860)
    if not g_things.isDatLoaded() then g_things.loadDat('/data/things/860/Tibia.dat') end
    local out = {}
    for cid = 100, 65535 do
      local tt = g_things.getThingType(cid, ThingCategoryItem)
      if tt and tt:getId() == cid then
        local p = 5
        if tt:isGround() then p = 0 elseif tt:isGroundBorder() then p = 1 elseif tt:isOnBottom() then p = 2 elseif tt:isOnTop() then p = 3 end
        out[#out + 1] = string.format('%d %d %d %d %d %d', cid, tt:getMinimapColor(),
          tt:isNotWalkable() and 1 or 0, tt:isNotPathable() and 1 or 0, p, tt:getGroundSpeed())
      end
    end
    g_resources.writeFileContents('/dump_itens.txt', table.concat(out, '\n'))
    g_app.exit()
  end, 3000)
end
