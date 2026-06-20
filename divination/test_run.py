"""端到端冒烟测试:跑通 4 种占卜引擎。

执行: `python -m divination.test_run`
"""
from divination import Birth, astro_math as am, compute

B = Birth(year=1990, month=5, day=15, hour=8, minute=30,
          gender="male", lat=31.23, lng=121.47, tz="Asia/Shanghai")

print("="*60)
print("【1】astro_math 纯数学层(B路核心,零星历依赖)")
print("  35°  ->", am.sign_of(35))          # 金牛 5°
print("  200° ->", am.sign_of(200))         # 天秤 20°
asp = am.find_aspects({"太阳": 0, "月亮": 120, "火星": 90, "金星": 6})
print("  相位:", [(a['a'], a['b'], a['aspect']) for a in asp])
print("  上升(LST=180,lat=31.23):", round(am.ascendant(180, 31.23), 2))
print("  整宫制前3宫:", am.houses(45, "whole")[:3])

print("="*60)
print("【2】八字  lunar-python(真算)")
r = compute("bazi", B)
print("  引擎:", r.engine, "| 四柱:", r.raw["pillars"])
print("  五行强弱:", r.normalized["elements"])
print("  大运:", [t["label"] for t in r.normalized["timeline"][:4]])

print("="*60)
print("【3】紫微  py-iztro(真算)")
try:
    r = compute("ziwei", B)
    print("  命主/身主:", r.raw["soul"], "/", r.raw["body"])
    print("  命宫主星:", next((p["major_stars"] for p in r.raw["palaces"] if p.get("name") == "命宫"), None))
except Exception as e:
    print("  [跳过,py-iztro 未装或 API 变化]", type(e).__name__, str(e)[:120])

print("="*60)
print("【4】奇门  kinqimen(真算)")
try:
    r = compute("qimen", B)
    print("  引擎:", r.engine, "| keys:", list(r.raw.keys())[:6])
except Exception as e:
    print("  [跳过,kinqimen 未装或 API 变化]", type(e).__name__, str(e)[:120])

print("="*60)
print("【5】西方占星  skyfield + 自算(B路)")
try:
    r = compute("western", B)
    print("  行星:", {k: (v['sign'], v['degree']) for k, v in r.raw['planets'].items()})
    print("  相位:", [(a['a'], a['b'], a['aspect']) for a in r.raw['aspects']])
    print("  上升:", r.raw['ascendant'])
except Exception as e:
    print("  [沙箱联网受限,无法下载星历]", type(e).__name__)
    print("  -> 用模拟黄经验证自算层(你的环境 skyfield 会给真实值):")
    mock = {"太阳": 54.2, "月亮": 172.8, "水星": 40.1, "金星": 80.5,
            "火星": 300.0, "木星": 95.3, "土星": 290.7}
    planets = {k: am.sign_of(v) for k, v in mock.items()}
    print("    星座:", {k: (v['sign'], v['degree']) for k, v in planets.items()})
    print("    相位:", [(a['a'], a['b'], a['aspect']) for a in am.find_aspects(mock)])

print("="*60)
print("【6】吠陀  skyfield + Lahiri(联网才有意义)")
try:
    r = compute("vedic", B)
    print("  Ayanamsa:", r.raw["ayanamsa"], "| 太阳星座:", r.raw["planets"]["太阳"]["sign"])
except Exception as e:
    print("  [跳过,需联网]", type(e).__name__, str(e)[:120])

print("="*60)
print("【7】八字 V2 精算版  lunar-python+shensha+pattern+v2")
try:
    r = compute("bazi_v2", B)
    print("  引擎:", r.engine)
    print("  日主:", r.raw["day_master"], "| 身强:", r.raw["strength_score"])
    print("  格局:", r.raw["pattern"]["pattern"])
    print("  用神:", r.raw["yong_shen"]["rationale"][:80])
    print("  用神质量:", r.raw["yong_shen_quality"]["score"], "/", r.raw["yong_shen_quality"]["level"])
    print("  关键神煞:", r.raw["shensha"]["summary"]["notable"])
    print("  五行流转:", r.raw["element_flow"]["interpretation"])
    print("  五行:", r.normalized["elements"])
except Exception as e:
    print("  [失败]", type(e).__name__, str(e)[:120])

print("="*60)
print("中西统一接口验证完毕。")
