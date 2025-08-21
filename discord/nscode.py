import html
from lark import Lark, Transformer, Tree
from dataclasses import dataclass
from lib import displayName, normalize

grammar = r"""
    tree: value*
    ?value: bold_tag
          | italic_tag
          | underline_tag
          | strike_tag
          | sub_tag
          | sup_tag
          | nation_tag
          | region_tag
          | proposal_tag
          | resolution_tag
          | default_spoiler_tag
          | spoiler_tag
          | url_tag
          | pre_tag
          | quote_tag
          | fragment

    fragment: TEXT

    bold_tag: "[b]" value+ "[/b]"
    italic_tag: "[i]" value+ "[/i]"
    underline_tag: "[u]" value+ "[/u]"
    strike_tag: "[strike]" value+ "[/strike]"
    sub_tag: "[sub]" value+ "[/sub]"
    sup_tag: "[sup]" value+ "[/sup]"
    nation_tag: "[nation" ("=" nation_flags)? "]" NAME "[/nation]"
    region_tag: "[region]" NAME "[/region]"
    proposal_tag: "[proposal=" PROPOSAL "]" value+ "[/proposal]"
    resolution_tag: "[resolution=" council "#" NUMBER "]" value+ "[/resolution]"
    default_spoiler_tag: "[spoiler]" value* "[/spoiler]"
    spoiler_tag: "[spoiler=" TEXT "]" value* "[/spoiler]"
    url_tag: "[url=" TEXT "]" value+ "[/url]"
    pre_tag: "[pre]" value+ "[/pre]"
    quote_tag: "[quote=" NAME ";" NUMBER "]" value+ "[/quote]"

    nation_flags: nation_flag ("+" nation_flag)*
    nation_flag: "noflag"
               | "noname"
               | "long"

    council: "GA"
           | "SC"
           | "UN"

    DIGIT: "0".."9"
    NUMBER: DIGIT+
    TEXT: /[^\[\]]+/
    NAME: /[A-Za-z0-9 _-]+/
    PROPOSAL: /[a-z0-9_-]+/
    """

def wrapNonEmpty(text: str, start: str, end: str):
    if text == "":
        return text
    
    return f"{start}{text}{end}"

class Tag:
    def render(self) -> str:
        return ""

@dataclass
class TextTag(Tag):
    text: str

    def render(self) -> str:
        return self.text

@dataclass
class BoldTag(Tag):
    children: list[Tag]

    def render(self) -> str:
        subtext = "".join([
            child.render() for child in self.children
        ])

        return "\n".join(
            [wrapNonEmpty(text, "**", "**") for text in subtext.split("\n")]
        )
    
@dataclass
class ItalicTag(Tag):
    children: list[Tag]

    def render(self) -> str:
        subtext = "".join([
            child.render() for child in self.children
        ])

        return "\n".join(
            [wrapNonEmpty(text, "*", "*") for text in subtext.split("\n")]
        )
    
@dataclass
class UnderlineTag(Tag):
    children: list[Tag]

    def render(self) -> str:
        subtext = "".join([
            child.render() for child in self.children
        ])

        return "\n".join(
            [wrapNonEmpty(text, "__", "__") for text in subtext.split("\n")]
        )
    
@dataclass
class StrikeTag(Tag):
    children: list[Tag]

    def render(self) -> str:
        subtext = "".join([
            child.render() for child in self.children
        ])

        return "\n".join(
            [wrapNonEmpty(text, "~~", "~~") for text in subtext.split("\n")]
        )
    
@dataclass
class SubTag(Tag):
    children: list[Tag]

    def render(self) -> str:
        # Only partially supported on Discord (only at the start of a line)
        # To avoid trouble, just render it as normal text.
        return "".join([
            child.render() for child in self.children
        ])
    
@dataclass
class SupTag(Tag):
    children: list[Tag]

    def render(self) -> str:
        # Not supported on Discord, just render it as normal text.
        return "".join([
            child.render() for child in self.children
        ])
    
@dataclass
class NationTag(Tag):
    name: str

    def render(self) -> str:
        return f"[{displayName(self.name)}](https://www.nationstates.net/nation={normalize(self.name)})"
    
@dataclass
class RegionTag(Tag):
    name: str

    def render(self) -> str:
        return f"[{self.name}](https://www.nationstates.net/region={normalize(self.name)})"
    
@dataclass
class ProposalTag(Tag):
    proposalId: str
    children: list[Tag]

    def render(self) -> str:
        subtext = "".join([
            child.render() for child in self.children
        ])

        return "\n".join(
            [wrapNonEmpty(text, "[", 
                f"](https://www.nationstates.net/page=UN_view_proposal/id={self.proposalId})"
            ) for text in subtext.split("\n")]
        )
    
@dataclass
class ResolutionTag(Tag):
    council: str
    resolutionId: str
    children: list[Tag]

    def render(self) -> str:
        subtext = "".join([
            child.render() for child in self.children
        ])

        page = f"page=WA_past_resolution/id={self.resolutionId}/council=1"
        if self.council == "SC":
            page = f"page=WA_past_resolution/id={self.resolutionId}/council=2"
        if self.council == "UN":
            page = f"page=WA_past_resolution/id={self.resolutionId}/un=1"

        return "\n".join(
            [wrapNonEmpty(text, "[", 
                f"](https://www.nationstates.net/{page})"
            ) for text in subtext.split("\n")]
        )
    
@dataclass
class UrlTag(Tag):
    url: str
    children: list[Tag]

    def render(self) -> str:
        subtext = "".join([
            child.render() for child in self.children
        ])

        return "\n".join(
            [wrapNonEmpty(text, "[", f"]({self.url})") for text in subtext.split("\n")]
        )
    
@dataclass
class PreTag(Tag):
    children: list[Tag]

    def render(self) -> str:
        subtext = "".join([
            child.render() for child in self.children
        ])

        return "\n".join(
            [wrapNonEmpty(text, "`", "`") for text in subtext.split("\n")]
        )
    
@dataclass
class QuoteTag(Tag):
    author: str
    id: str
    children: list[Tag]

    def render(self) -> str:
        subtext = "".join([
            child.render() for child in self.children
        ])

        # Limit quotes to 256 characters
        if len(subtext) > 256:
            subtext = subtext[:256] + "..."

        quoted = "\n".join(
            [wrapNonEmpty(text, "> ", "") for text in subtext.split("\n")]
        )

        if self.author == "0" or self.id == "0":
            return quoted
        
        return f"**[Quoted from {displayName(self.author)}](https://www.nationstates.net/page=rmb/postid={self.id})**:\n{quoted}"

@dataclass
class SpoilerTag(Tag):
    label: str | None
    children: list[Tag]

    def render(self) -> str:
        # ignore spoiler
        return "".join([
            child.render() for child in self.children
        ])
    
@dataclass
class NsCodeTree:
    children: list[Tag]

    def render(self) -> str:
        return "".join([
            child.render() for child in self.children
        ])

class NsCodeTransformer(Transformer):
    def fragment(self, items):
        return TextTag(items[0].value)
    
    def bold_tag(self, items):
        return BoldTag(items[1:-1])
    
    def italic_tag(self, items):
        return ItalicTag(items[1:-1])
    
    def underline_tag(self, items):
        return UnderlineTag(items[1:-1])
    
    def strike_tag(self, items):
        return StrikeTag(items[1:-1])
    
    def sub_tag(self, items):
        return SubTag(items[1:-1])
    
    def sup_tag(self, items):
        return SupTag(items[1:-1])
    
    def nation_tag(self, items):
        # just ignore flags
        return NationTag(items[-2].value)
    
    def region_tag(self, items):
        return RegionTag(items[-2].value)
    
    def proposal_tag(self, items):
        return ProposalTag(items[1].value, items[3:-1])
    
    def resolution_tag(self, items):
        return ResolutionTag(items[1].value, items[3].value, items[5:-1])
    
    def url_tag(self, items):
        return UrlTag(items[1].value, items[3:-1])
    
    def pre_tag(self, items):
        return PreTag(items[1:-1])
    
    def quote_tag(self, items):
        return QuoteTag(items[1].value, items[3].value, items[5:-1])

    def default_spoiler_tag(self, items):
        return SpoilerTag(None, items[1:-1])
    
    def spoiler_tag(self, items):
        return SpoilerTag(items[1].value, items[3:-1])
    
    def tree(self, items):
        return NsCodeTree(items)

def parseNsCode(content: str) -> NsCodeTree:
    unicodeContent = html.unescape(content)
    parser = Lark(grammar, 
                  start='tree', 
                  parser='lalr', 
                  keep_all_tokens=True, 
                  transformer=NsCodeTransformer())

    return parser.parse(unicodeContent)