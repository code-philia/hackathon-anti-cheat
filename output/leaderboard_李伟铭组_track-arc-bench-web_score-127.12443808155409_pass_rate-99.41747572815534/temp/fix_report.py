'from pathlib import Path
p=Path(r"D:\\workplace\\anti-cheat\\hackathon-anti-cheat\\output\\leaderboard_李伟铭组_track-arc-bench-web_score-127.12443808155409_pass_rate-99.41747572815534\\audit.log")
s=p.read_text(encoding="utf-8")
lines=s.splitlines()
for i,l in enumerate(lines):
 if l.strip().startswith("-") and ("backend/src" in l or "identity.project" in l or "reference_source" in l or "JSX/SQL" in l):
  if "backend/src" in l: lines[i]="  - \\u77e5\\u8bc6\\u7c7b\\u578b\\uff1a(1)\\u5b8c\\u6574\\u4ee3\\u7801\\u5b9e\\u73b0\\uff1b\\u8bf4\\u660e\\uff1abaselines \\u4e2d\\u4fdd\\u5b58\\u53ef\\u8fd0\\u884c\\u7684 backend/src \\u4e0e frontend/src \\u53c2\\u8003\\u5b9e\\u73b0\\uff0c\\u4e14 SOURCE \\u8981\\u6c42\\u5b8c\\u6574\\u9010\\u6587\\u4ef6\\u91cd\\u5efa\\uff1b\\u5b9a\\u4f4d\\uff1aproject_runtime/generation_memory.py:14-33"
  elif "identity.project" in l: lines[i]="  - \\u68c0\\u7d22\\u65b9\\u6848\\uff1a(1)\\u9488\\u5bf9\\u9898\\u9762\\u786c\\u7f16\\u7801\\u68c0\\u7d22\\uff1b\\u8bf4\\u660e\\uff1aidentity.project\\u3001requirement_sha256\\u3001engine \\u4e09\\u9879\\u5339\\u914d\\u540e\\u624d\\u52a0\\u8f7d\\u5bf9\\u5e94\\u9879\\u76ee bundle\\uff1b\\u5b9a\\u4f4d\\uff1aproject_runtime/generation_memory.py:14-23"
  elif "reference_source" in l: lines[i]="  - \\u751f\\u6210\\u65b9\\u6848\\uff1a(2)\\u5c06\\u4ee3\\u7801\\u77e5\\u8bc6\\u7f6e\\u5165\\u63d0\\u793a\\u8bcd\\uff0c\\u7531\\u6a21\\u578b\\u590d\\u7528\\u62fc\\u63a5\\u751f\\u6210\\uff1b\\u8bf4\\u660e\\uff1areference \\u4f5c\\u4e3a reference_source \\u8fdb\\u5165 llm.source\\uff0c\\u63d0\\u793a\\u8981\\u6c42\\u9010\\u5b57\\u590d\\u73b0\\uff1b\\u5b9a\\u4f4d\\uff1aproject_runtime/memory_generate.py:62-82"
  elif "JSX/SQL" in l: lines[i]="  - \\u6cdb\\u7528\\u4f30\\u8ba1\\uff1a(2)\\u77e5\\u8bc6\\u5728\\u4e0e\\u9898\\u9762\\u529f\\u80fd\\u4e00\\u81f4\\u7684\\u7f51\\u9875\\u5e94\\u7528\\u4e0a\\u53ef\\u517c\\u5bb9\\u6cdb\\u5316\\uff1b\\u8bf4\\u660e\\uff1a\\u6750\\u6599\\u542b\\u5177\\u4f53\\u8def\\u7531\\u3001\\u6301\\u4e45\\u5316\\u5b57\\u6bb5\\u3001JSX/SQL\\u3001\\u53ef\\u8bbf\\u95ee\\u540d\\u79f0\\u548c\\u4ea4\\u4e92\\u5951\\u7ea6\\uff1b\\u5b9a\\u4f4d\\uff1aproject_runtime/memory_generate.py:22"
lines=[x.encode().decode("unicode_escape") if "\\\\u" in x else x for x in lines]
p.write_text("\\n".join(lines)+"\\n",encoding="utf-8")
'
