from divination import Birth, compute
b = Birth(year=1990, month=5, day=15, hour=8, minute=30, gender="male",
          lat=31.23, lng=121.47, tz="Asia/Shanghai")
print("【八字】", compute("bazi", b).raw["pillars"])
zw = compute("ziwei", b); print("【紫微】命主", zw.raw["soul"], "身主", zw.raw["body"])
w = compute("western", b)
print("【西方】上升", w.raw["ascendant"]["sign"], round(w.raw["ascendant"]["lon"],2),
      "| 天顶", w.raw["midheaven"]["sign"])
print("  行星:", {k:(v['sign'],round(v['degree'],1)) for k,v in w.raw["planets"].items()})
print("  Placidus 1-4宫:", [(h["house"],h["sign"],h["cusp_lon"]) for h in w.raw["houses"][:4]])
print("  相位:", [(a['a'],a['b'],a['aspect']) for a in w.raw["aspects"]][:5])
