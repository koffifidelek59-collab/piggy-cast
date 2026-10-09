-- Pandoc Lua filter: maps LaTeX constructs of niger_policy_memo.tex to Word styles.

local function strip_style(attr)
  if attr and attr.attributes then attr.attributes.style = nil end
end

function Span(el)
  local st = el.attributes.style
  if st and st:match("color:%s*ans") then
    el.attributes.style = nil
    el.attributes["custom-style"] = "Answer"
    return el
  end
  if st then
    strip_style(el)
    return el.content
  end
end

function Div(el)
  if el.classes:includes("titlepage") then
    return {}
  end
  if el.classes:includes("keybox") then
    -- first paragraph is the box title
    local blocks = el.content
    if #blocks > 0 and blocks[1].t == "Para" then
      blocks[1] = pandoc.Div({ pandoc.Para({ pandoc.Strong(pandoc.utils.stringify(blocks[1])) }) },
        pandoc.Attr("", {}, { ["custom-style"] = "Key Box Title" }))
    end
    return pandoc.Div(blocks, pandoc.Attr("", {}, { ["custom-style"] = "Key Box" }))
  end
  if el.classes:includes("center") then
    if pandoc.utils.stringify(el):match("^End of Subject") then
      return pandoc.Div(el.content, pandoc.Attr("", {}, { ["custom-style"] = "End Note" }))
    end
    return pandoc.Div(el.content, pandoc.Attr("", {}, { ["custom-style"] = "Centered" }))
  end
end

function RawBlock(el)
  if el.format == "latex" or el.format == "tex" then
    if el.text:match("\\clearpage") or el.text:match("\\newpage") then
      return pandoc.RawBlock("openxml", '<w:p><w:r><w:br w:type="page"/></w:r></w:p>')
    end
    return {}
  end
end

function RawInline(el)
  if el.format == "latex" or el.format == "tex" then
    return {}
  end
end

function Para(el)
  if pandoc.utils.stringify(el) == "PAGEBREAKMARKER" then
    return {}  -- the References heading gets "page break before" in post-processing
  end
end

function BlockQuote(el)
  local blocks = el.content
  local out = {}
  for i, b in ipairs(blocks) do
    if i == 1 and b.t == "Para" and #b.content == 1 and b.content[1].t == "Strong" then
      table.insert(out, pandoc.Div({ b }, pandoc.Attr("", {}, { ["custom-style"] = "Key Box Title" })))
    else
      table.insert(out, b)
    end
  end
  return pandoc.Div(out, pandoc.Attr("", {}, { ["custom-style"] = "Key Box" }))
end

function Inlines(inlines)
  local out = pandoc.List()
  for i, el in ipairs(inlines) do
    if el.t == "Str" and el.text == "LBRK" then
      if #out > 0 and (out[#out].t == "Space" or out[#out].t == "SoftBreak") then out:remove(#out) end
      out:insert(pandoc.LineBreak())
    elseif (el.t == "Space" or el.t == "SoftBreak") and #out > 0 and out[#out].t == "LineBreak" then
      -- drop space after a line break
    else
      out:insert(el)
    end
  end
  return out
end

-- Numbered paragraphs run continuously through the memo (1, 2, 3, ...);
-- lettered lists (recommendations) keep their own numbering.
local para_counter = 0
function OrderedList(el)
  if el.listAttributes.style == "Decimal" or el.listAttributes.style == "DefaultStyle" then
    el.listAttributes.start = para_counter + 1
    para_counter = para_counter + #el.content
  end
  return el
end
