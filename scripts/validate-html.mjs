#!/usr/bin/env node
// HTML 静态自检：验证 office-visual-spec 的可编辑 HTML 契约
import { readFileSync } from "node:fs";

try {
  const file = process.argv[2];
  if (!file) {
    console.error("出错了：没有提供 HTML 文件路径");
    console.error("下一步：运行 node scripts/validate-html.mjs <html>");
    process.exit(2);
  }

  const html = readFileSync(file, "utf-8");
  const checks = [];
  const ok = (name, pass, detail = "") => {
    checks.push({ name, pass, detail });
  };

  ok("存在 <style>", /<style[\s>]/i.test(html));
  ok("无远程样式表", !/<link[^>]+rel=["']stylesheet["'][^>]*>/i.test(html));
  ok("无 @import", !/@import/i.test(html));
    const styleBlock = (html.match(/<style[^>]*>([\s\S]*?)<\/style>/i) || [])[1] || "";
  ok("无远程字体", !/fonts\.googleapis|fonts\.gstatic|cdnjs|unpkg|jsdelivr/i.test(html) && !/url\(\s*['"]?https?:\/\//i.test(styleBlock));

  const sectionSheets = (html.match(/<section[^>]*class="[^"]*sheet/i) || []).length;
  const divSheets = (html.match(/<div[^>]*class="[^"]*sheet/i) || []).length;
  ok("分页容器使用 div.sheet", sectionSheets === 0, `section.sheet=${sectionSheets}, div.sheet=${divSheets}`);

  if (divSheets > 0) {
    ok("存在 page-break-after", /page-break-after\s*:\s*always/i.test(html));
    ok("存在 break-after: page", /break-after\s*:\s*page/i.test(html));
  }

  const hasCards = /class="[^"]*(card|quote-card|step|timeline)/i.test(html);
  if (hasCards) {
    ok("卡片使用 break-inside: avoid", /break-inside\s*:\s*avoid/i.test(html));
  } else {
    ok("无卡片，跳过 break-inside 检查", true, "no card elements");
  }
  ok("无强制水印", !/AI辅助生成/.test(html));


  const isPptWeb = /id="stage"/.test(html) || /data-anim/.test(html);
  if (isPptWeb) {
    ok("ppt-web 使用固定 1280x720 舞台", /1280px/.test(styleBlock) && /720px/.test(styleBlock));
    ok("ppt-web 样式无硬编码强调色", !/#E4573D/i.test(styleBlock.replace(/--accent-bright:\s*#E4573D;?/g, "")));
    ok("ppt-web 支持 reduced motion", /prefers-reduced-motion/.test(html));
  }

  let failed = false;
  for (const c of checks) {
    console.log(`${c.pass ? "✅" : "❌"} ${c.name}${c.detail ? ` (${c.detail})` : ""}`);
    if (!c.pass) failed = true;
  }

  process.exit(failed ? 1 : 0);
} catch (e) {
  console.error("出错了：" + (e && e.message ? e.message : String(e)));
  console.error("下一步：请检查 HTML 文件是否存在、路径是否正确。");
  process.exit(1);
}
