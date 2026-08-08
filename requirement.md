# GeoLens - Founding Document

> **Working Name:** GeoLens
> **Status:** Pre-build / Idea stage
> **Date:** August 2026

---

## 1. What Is GeoLens?

I'm building an AI-powered location discovery platform. The core idea: when I'm watching a video and I see a place I'm curious about, I can use GeoLens to find out where that place is.

**One-sentence pitch:** An AI-powered platform that helps people discover where any scene in a video was filmed by analyzing visual and contextual clues.

---

## 2. The Problem I'm Solving

### 2.1 The Curiosity Gap

Billions of videos are watched daily across YouTube, Instagram, TikTok, documentaries, travel films, drone footage, and educational content. These videos showcase places around the world - mountains, waterfalls, villages, beaches, temples, trails, scenic roads, forests, cafes, castles - yet viewers are frequently left with one unanswered question:

> "Where exactly is this?"

I've experienced this myself. I watch a video, I see an incredible place, and I have no easy way to figure out where it is.

### 2.2 How People Currently Try to Answer This

- Reading through YouTube comments hoping someone identified the location
- Posting on Reddit asking for help
- Using reverse image search (Google Images, TinEye)
- Using Google Lens on a screenshot
- Searching the video description and title for clues
- Guessing based on visible landmarks
- Asking an AI chatbot with a screenshot

### 2.3 Why These Methods Fall Short

- They are slow and manual
- Results are inconsistent and often incorrect
- They cannot combine multiple types of evidence
- They work for famous landmarks but fail for everyday places
- No single tool is designed specifically for this use case

### 2.4 Why This Is Hard

A single video frame rarely contains enough information to identify a location on its own. Location clues are fragmented across many sources:

- Visual elements in the frame (terrain, vegetation, architecture, signage, road markings, sun position)
- Audio and spoken dialogue
- Text overlays within the video
- Video metadata (title, description, tags)
- The creator's channel history and past uploads
- Related content from the same region
- Geographic and topographic patterns

Humans naturally triangulate from multiple clues. Existing tools generally process only one input (a single image) in isolation. I want to build something that reasons the way a human would - combining many weak signals into a strong conclusion.

---

## 3. What Already Exists and Why It's Not Enough

I've looked at what's out there. Things do exist - but none of them solve this problem well.

| Tool | What It Does | Why It Falls Short |
|---|---|---|
| **Google Lens** | Identifies objects, products, landmarks in a photo | Recognizes what's in the image, not where it was filmed. Works for the Eiffel Tower, fails for an unnamed valley. |
| **GeoSpy** | AI geolocation from a single image | Single-image analysis only. No video context, no channel history, no triangulation across evidence. |
| **Pic2Map** | Reads EXIF GPS data from photos | Only works if the photo has embedded GPS metadata. Most video screenshots don't. |
| **Google Maps / Earth** | Satellite imagery and street view | Requires you to already know roughly where to look. It's a verification tool, not a discovery tool. |
| **Asking ChatGPT/Claude with a screenshot** | General AI reasoning about an image | Better than nothing, but works from a single frame with zero context. No access to the video's metadata, the creator's history, or related content. |
| **GeoGuessr** | Gamified location guessing | It's a game, not a tool. Proves people enjoy location discovery but doesn't solve the problem. |
| **Reddit (r/whereisthis, r/geolocating)** | Human-powered location identification | Slow (hours to days), unreliable, depends on someone knowledgeable seeing your post. |

### The Gap

Every existing tool treats this as a single-image recognition problem. None of them do what a curious human would naturally do: pause the video, look at the terrain, check the video title, look at what country the creator usually films in, scan for text in the frame, notice the style of the road markings, and combine all of that into a conclusion.

That multi-signal reasoning is what I want GeoLens to do. That's the gap.

---

## 4. The Core Differentiator: Multi-Signal Triangulation

This deserves its own section because it's the single most important thing that separates GeoLens from everything else.

### The Idea

A single frame is ambiguous. A mountain could be in Norway or New Zealand. A beach could be Thailand or Brazil. But when I combine multiple signals, the possibilities narrow dramatically:

- **Frame analysis** tells me: tropical vegetation, terraced hills, a narrow-gauge railway track
- **Video metadata** tells me: title says "hill country train ride"
- **Channel context** tells me: this creator's last 8 videos were all from Sri Lanka
- **Text in video** tells me: a sign partially visible says something in Sinhala script
- **Related videos** tell me: other creators filming the same railway all tag it as "Ella to Kandy"

Each signal alone is weak. Combined, they point to one place with high confidence.

### Why This Matters

This is what makes GeoLens defensible. Anyone can send a screenshot to an AI and ask "where is this?" The results will be mediocre because the AI only has one frame. My system has access to the full evidence chain, and the quality of that triangulation is what users will pay for and what competitors can't easily replicate without doing the same deep integration work.

### What a Good Result Looks Like

Here's a concrete example of the kind of output I want GeoLens to produce:

```
Location: Ella, Sri Lanka
Region: Badulla District, Uva Province
Coordinates: 6.8667° N, 81.0466° E
Confidence: High (4 of 5 evidence signals aligned)

Evidence:
  1. Vegetation matches Sri Lankan central highlands (tropical montane)
  2. Narrow-gauge railway visible — matches Ella-Badulla railway line
  3. Creator's last 5 videos all tagged "Sri Lanka"
  4. Video title contains "hill country train ride"
  5. Sinhala script partially visible on platform sign

[View on Google Maps]  [View on Google Earth]  [Street View nearby]
```

This is what I mean by a trustworthy, explainable answer. The user can see exactly why the system reached this conclusion and judge the confidence for themselves.

---

## 5. Concrete User Scenarios

### Scenario 1: Quick Lookup

> I'm watching a drone video on YouTube. At 4:32, the drone flies over a stunning valley with a river cutting through green hills. I want to know where this is.
>
> I click the GeoLens button. 20 seconds later, a panel appears on the YouTube page:
> - "Zuluk Valley, East Sikkim, India"
> - Confidence: High
> - Evidence: terrain matches Eastern Himalayan foothills, creator's channel focuses on Northeast India, video description mentions "Silk Route"
> - A Google Maps link
>
> I got my answer without leaving the video. I save it to my history and keep watching.

### Scenario 2: Full Video Scan

> I just finished watching a 25-minute travel vlog that covered multiple locations across Sri Lanka. I want to know where all of those places were.
>
> I click "Scan Full Video." GeoLens starts working. I can see the progress: "Reading video... analyzing frames... checking 47 comments... pulling creator's channel history... cross-referencing 3 related videos..."
>
> A few minutes later, the result appears: a complete location map.
>
> The YouTube timeline is marked with 8 location segments. Each one has a name, coordinates, confidence, and evidence. The agent found locations by combining frame analysis with a comment that said "the waterfall at 12:30 is Ravana Falls!", metadata from the creator's Instagram linked in the description, and the fact that the creator's last 6 videos were all tagged "Sri Lanka Southern Province."
>
> I see an interactive map with all 8 locations plotted. I can click any pin to jump to that moment in the video. The whole thing is shareable - I copy the link and post it in the video's comments: "I mapped every location in this video using GeoLens."
>
> That comment gets 200 likes. 50 people install GeoLens.

That's the difference between a utility and a viral product. Quick Lookup keeps people using it. Full Video Scan makes people share it.

---

## 6. YouTube Integration & UX Vision

I don't want GeoLens to be just a popup that floats over the browser. I want it to feel like a native part of the YouTube experience.

### Injected UI Elements

The Chrome extension should inject UI directly into the YouTube page:

- **Timeline markers** - Visual indicators on the YouTube progress bar showing which segments of the video contain identifiable locations. Like chapters, but for places.
- **Location frame highlights** - When a location-rich scene is playing, a subtle indicator appears on or near the video player showing that GeoLens has information about this scene.
- **Side panel or overlay** - When activated, a panel shows the location details (map render, coordinates, evidence, confidence) without taking the user away from the video.
- **Location cards** - Rich visual cards showing a satellite/map render of the identified location, the coordinates, the place name, region, and country. These should feel polished and shareable.

### The Key UX Idea

The user shouldn't have to pause the video, take a screenshot, and upload it somewhere. The experience should be:

1. I'm watching a video
2. I see a place I'm curious about
3. I click (or the timeline already shows me)
4. I get the answer right there, inline, without leaving YouTube

### Progressive Disclosure

- At a glance: location name + confidence badge on the timeline
- One click: full location card with map, coordinates, evidence
- Deep dive: Google Maps/Earth link, nearby attractions, save to history, share

---

## 7. Platform Vision: Beyond Single Lookups

GeoLens starts as a tool for answering "where is this?" but I want it to grow into a platform.

### History

Every lookup I do gets saved to my personal GeoLens history. Over time, this becomes my personal map of every interesting place I've discovered through videos. I can:
- Browse my past discoveries
- See them plotted on a world map
- Revisit the source video
- Organize by region, date, or category

### Sharing

When I discover a location, I should be able to share it. A GeoLens result becomes a shareable link or card that includes the location, the evidence, and a link back to the source video moment. Think of it like sharing a pin on Pinterest, but for places discovered in videos.

### Community & Marketplace

As more people use GeoLens, a network effect develops:

- **Hot searches** - What locations are people discovering right now? Trending places surfaced from the community's collective curiosity. "This week, 2,400 people searched for locations from this viral drone video."
- **Popular discoveries** - A feed of the most interesting or surprising location discoveries.
- **Browse by region** - "Show me all the places people have discovered in Patagonia this month."
- **Creator leaderboards** - Which YouTube creators' videos generate the most location discoveries?
- **Crowdsourced accuracy** - Other users can confirm or correct location results, improving accuracy over time.

### The Flywheel

More users -> more lookups -> more data -> better accuracy -> more useful results -> more users. And the shared discovery layer makes GeoLens a destination in itself, not just a utility.

---

## 8. The Opportunity

### 8.1 Market Signals

- Millions of daily searches for filming locations
- Thousands of Reddit posts asking "where was this filmed?"
- YouTube comments frequently contain "where is this?" questions
- Creators are repeatedly asked about their filming locations
- GeoGuessr's popularity demonstrates interest in location discovery as an activity
- Travel content is among the fastest-growing video categories
- No dedicated product currently serves this specific need

### 8.2 Why Now

- Computer vision capabilities have advanced significantly
- Large language models can reason across multiple forms of evidence
- Multimodal AI can process images, audio, text, and metadata together
- Video content volume continues to grow rapidly
- User expectations for AI-powered answers are rising

---

## 9. Who Am I Building This For?

### Consumers

| Persona | Motivation |
|---|---|
| Travel enthusiasts | Discover destinations seen in videos |
| Drone hobbyists | Identify locations from aerial footage |
| Photographers | Find photography spots seen in content |
| Hikers and outdoor enthusiasts | Identify trails and viewpoints |
| Documentary viewers | Learn where scenes were filmed |
| Geography enthusiasts | General curiosity about places |
| Film and TV fans | Discover filming locations |

### Professionals

| Persona | Motivation |
|---|---|
| Travel content creators | Generate location lists for their audiences |
| Researchers | Study locations shown in video content |
| Journalists | Verify where footage was actually filmed |
| OSINT analysts | Geographic verification of video evidence |

### Potential Enterprise Customers

| Organization Type | Use Case |
|---|---|
| News organizations | Video footage verification |
| Insurance companies | Claims investigation |
| NGOs | Disaster response and field verification |
| Research institutions | Geographic analysis |
| AI companies | Integrating location inference into their products |

---

## 10. What GeoLens Should Provide to Users

When someone wants to know where a video scene was filmed, GeoLens should return:

- **Location identification** - the most likely place (name, region, country)
- **Coordinates** - latitude and longitude when possible
- **Confidence level** - how certain the system is about the result
- **Reasoning** - an explanation of what evidence led to this conclusion
- **Map render** - a visual satellite or map view of the identified location
- **Map link** - a way to view the location on Google Maps / Earth
- **Timeline context** - which moments in the video correspond to this location

I want to emphasize trustworthy, explainable answers over false precision. A transparent "medium confidence" result is more valuable than a confident wrong answer.

---

## 11. My Product Principles

- **Evidence over guessing** - never present certainty where it doesn't exist
- **Transparency** - users should understand why a conclusion was reached
- **Curiosity-driven** - this product exists to satisfy natural human curiosity about places
- **Discovery** - I want this to be a platform for learning about the world, not just a utility
- **Native feel** - the experience should feel integrated into YouTube, not bolted on
- **Progressive depth** - simple answer at a glance, full evidence on demand

---

## 12. Positioning

### GeoLens is:
- A location inference platform focused on video content
- An integrated YouTube experience for geographic discovery
- A growing platform of shared location discoveries

### GeoLens is not:
- A reverse image search engine
- A map application
- A travel booking platform
- A generic AI chatbot

### Differentiation
Most existing tools treat this as a single-image recognition problem. GeoLens combines multiple evidence signals (frame analysis, video metadata, channel context, related content) to triangulate locations. That multi-signal approach, combined with a native YouTube integration and a shared discovery platform, is what sets it apart.

---

## 13. Business Model Options

I've identified multiple monetization paths. Not all are required for launch - these represent options to explore. All pricing figures below are assumptions to validate, not researched numbers.

### Option A: Freemium Consumer Product

A free tier with limited lookups per day (e.g., 5/day) with basic results (country + region + confidence). A paid tier (thinking $8-15/month range, but needs validation) with unlimited lookups, exact coordinates, detailed evidence reports, full history, timeline scanning, and export features.

### Option B: API Platform

Expose the location inference engine as an API that other products can integrate. Potential customers include travel apps, AI assistants, video platforms, research tools, and media companies. Per-request pricing (thinking $0.05 - $0.50 range depending on accuracy tier, but needs validation against actual AI API costs).

This is potentially the highest-scale opportunity. The vision: any AI assistant asked "Where was this filmed?" calls my API.

### Option C: Creator Tools

A SaaS product for video creators. Upload a video, automatically detect all locations shown, generate a formatted location list with map that creators can paste into video descriptions. Solves the "where is this?" comment problem for creators.

### Option D: Affiliate Revenue

When a location is identified, users are often interested in visiting. Recommendations for hotels, tours, activities, and attractions near the identified location could generate affiliate revenue. This works because users who just identified a location they're curious about represent high-intent traffic.

### Option E: Enterprise

Organizations that need geographic verification at scale (journalism, OSINT, insurance, disaster response, environmental monitoring, academic research). These customers typically pay significantly more than consumers.

### Option F: B2B Infrastructure

Video AI companies that need geolocation capabilities could license GeoLens rather than building it themselves.

### Unit Economics: The Open Question

This is the fundamental startup question I need to answer early: **does the math work?**

Every lookup costs me money in AI API calls. A full multi-agent pipeline might cost $0.05-0.25 per lookup (this is a guess - I need to measure it). On the free tier, I'm giving away 5 lookups/day. If I have 1,000 free users doing 3 lookups/day, that's 3,000 lookups/day, costing me potentially $150-750/day in AI costs alone before a single person pays me anything.

Questions I need to model out:

- What does a single lookup actually cost in AI API calls? (measure this as soon as the pipeline works)
- At what free-to-paid conversion rate do paid users cover the cost of free users?
- How much does caching reduce effective cost per lookup?
- Is there a cheaper pipeline configuration that gives "good enough" results for free-tier users, with the full expensive pipeline reserved for paid users?
- At what scale does the infrastructure cost (servers, databases) start to matter relative to AI API costs?

I don't need answers before building the MVP, but I need to be measuring from day one so I can model this out with real numbers.

---

## 14. MVP Concept

### What "MVP" Means Here

I want to validate demand as fast as possible. The MVP is the smallest thing I can ship to answer one question: **do people actually want this enough to use it repeatedly?**

I'm taking a "Wizard of Oz" approach - the product should feel like magic to the user, even if the backend is slow, expensive, or partially manual behind the scenes. I'm not optimizing for speed or cost yet. I'm optimizing for: does the output satisfy curiosity?

### Platform Scope

**MVP is YouTube only.** I'm not building for Instagram, TikTok, Vimeo, or anything else right now. YouTube is where the richest context lives (titles, descriptions, tags, channel history, related videos) and where most travel/drone content is consumed. If the product works on YouTube and usage validates the idea, I'll expand to other platforms based on what users actually ask for.

### Two Modes

GeoLens has two core modes. Both use the same agent harness and multi-signal pipeline, just at different depth.

**Mode 1: Quick Lookup**
I'm watching a video, I see a place I'm curious about, I click the button. The system captures the current frame, pulls video context, and returns the location in 15-30 seconds. This is the "Shazam moment" - fast, in the flow, instant gratification.

**Mode 2: Full Video Scan**
I want to know every location in the entire video. I activate the scan, and the agent goes deep - scrubs through the video, reads comments, pulls creator history, cross-references related videos, analyzes metadata - and produces a complete location map of every identifiable place in the video with timestamps. This takes longer (minutes, not seconds) but the output is dramatically richer: a full interactive timeline/map of all locations, evidence for each, coordinates, the whole picture.

Full Video Scan is the viral mode. The output - "GeoLens found 14 locations across 3 countries in this 20-minute drone video, here's the map" - is inherently shareable and impressive. This is what people screenshot and post. Quick Lookup is the daily utility that keeps people coming back.

Both modes share the same backend. Quick Lookup runs a subset of the pipeline on one frame. Full Video Scan runs the full pipeline across the entire video. The agent harness handles both - it's just a question of scope.

For MVP, I'll start with Quick Lookup since it's simpler to build and validates the core experience. Full Video Scan comes right after as the feature that drives virality and sharing.

### What's IN the MVP

- **Chrome extension** that injects a "Find Location" button/icon into the YouTube player area
- **Single-frame lookup** - I click the button, it captures the current frame I'm looking at
- **Context gathering** - the backend also pulls whatever it can from the video page: title, description, tags, channel name, channel's recent uploads
- **AI processing** - the backend runs the agent pipeline (details in Section 15) and returns a result
- **Results panel** - an inline panel on the YouTube page showing: location name, region, country, coordinates, confidence level, evidence summary, and a Google Maps link
- **Basic history** - my past lookups are saved and I can see them in the extension popup
- **Free tier limit** - 5 lookups per day on free, enough to validate engagement without running up AI costs
- **Basic analytics** - track installs, lookups, return visits, and which videos people use it on

### What's NOT in the MVP

These are features I want eventually but I'm deliberately cutting from v1:

- No Full Video Scan mode yet (this is the immediate next feature after MVP validates)
- No sharing or social features
- No community layer, hot searches, or marketplace
- No pro/paid tier (everyone gets 5/day free)
- No affiliate recommendations
- No API
- No mobile app
- No creator tools
- No polished location cards or satellite renders (a clean text result with a map link is enough)

### The Failure Case

The system won't always be able to identify a location. This will happen a lot, especially early on. When it can't, I need to handle it honestly:

- Show what the system was able to determine (e.g., "likely Southeast Asia based on vegetation and architecture, but I couldn't narrow it further")
- Show the confidence as "Low" with the partial evidence it did find
- Never make up a specific location when the evidence doesn't support one
- Optionally suggest: "This result is uncertain. You could try a different frame from this video."

Handling failure well is critical. A system that says "I'm not sure, here's what I do know" builds trust. A system that confidently returns the wrong location destroys it.

### What "Good Enough" Looks Like

I don't need perfect accuracy to launch the MVP. Here's my bar:

- **Famous landmarks and well-known places** - should be correct almost always. This is table stakes.
- **Places with strong contextual clues** (creator regularly films in one country, title mentions a region, visible text in local language) - should get the right country/region most of the time, exact location sometimes.
- **Obscure locations with minimal context** - getting the right country or region is a win. Exact coordinates are a bonus.
- **Overall target** - if the system gives a useful answer (right country/region or better) on roughly 60-70% of lookups on travel/drone content, that's good enough to validate demand. I can improve accuracy over time.

The key insight: users don't need GPS precision to be satisfied. "This is in the Dolomites, Italy, likely near Seceda based on the ridgeline" is a great answer even without exact coordinates.

### Acceptable Performance

- A lookup can take **15-30 seconds** for the MVP. This is an AI pipeline doing real reasoning, not a database lookup. Users will wait if the answer is good.
- Over 60 seconds starts to feel broken. I'd rather return a partial result than make someone wait 2 minutes.
- I should show a progress indicator so the user knows it's working, not frozen.

### First Users

I need to get the MVP in front of real users to validate. My plan for initial distribution:

- **Reddit** - post in r/travel, r/drones, r/whereisthis, r/geoguessr, r/geography, r/youtube. These communities are literally full of people asking the exact question I'm solving.
- **YouTube comments** - find popular travel/drone videos with "where is this?" comments and reply with the tool (carefully, not spammy).
- **Chrome Web Store** - list it with good keywords so organic discovery can happen.
- **Personal network** - share with friends who watch travel content.
- **Product Hunt** - launch when the extension is polished enough.

I'm not spending money on ads for the MVP. If the product is useful, these organic channels should be enough to validate.

### Authentication and Rate Limiting

I need a way to enforce the 5 lookups/day limit and persist user history. This means some form of user identity. Options to consider:

- **Google sign-in** - simplest for users since they're already on YouTube and likely signed into Google. Also gives me a real user identity for history, future sharing, and cross-device sync.
- **Extension-level anonymous tracking** - a generated ID stored in the extension. Simpler to implement, no sign-in friction, but history is lost if the user reinstalls and I can't do cross-device.
- **Email-based accounts** - standard signup flow. More friction but full control over the user relationship.

This is a decision to make during implementation. The key requirement: I need to count lookups per user per day and store history tied to a user.

### User Feedback Loop

Every result should include a simple **thumbs up / thumbs down**. This is critical for two reasons:

1. **Accuracy tracking** - it's the only way I'll know if the system is actually giving useful answers. Without this, I'm guessing about quality.
2. **Training data** - over time, confirmed-correct results become a dataset I can use to evaluate model changes, test new pipeline configurations, and potentially fine-tune. Every thumbs-up is a labeled example.

Optionally, on a thumbs-down, let the user say what the actual location was if they know it. That's even more valuable - it's a correction I can learn from.

This feedback loop is what turns the product from a static tool into a system that gets better over time.

### Edge Cases

Not every video contains a real-world location. The system needs to handle these gracefully:

- **Non-location content** - gaming footage, screen recordings, tutorials, talking-head videos, animations. The system should recognize "this frame doesn't contain a real-world location" and say so, rather than hallucinating a place.
- **Indoor scenes** - a restaurant interior, a hotel room, a museum. Might be identifiable from context (video title, signage) but the frame alone won't help. The system should lean heavily on context signals for these.
- **Heavily edited or stylized footage** - color-graded, filtered, or composited video. May confuse visual analysis. Should lower confidence accordingly.
- **Stock footage** - some creators use stock footage that doesn't match their actual filming location. The system should be aware this is possible.

The general principle: if the frame doesn't look like a real-world outdoor or identifiable indoor location, say so. Don't force an answer.

### Caching

If a travel video goes viral and thousands of people all click "Find Location" on the same video at similar timestamps, I don't want to run the full agent pipeline thousands of times. That would burn through AI costs for identical results.

I need a caching layer:

- **By video + timestamp range** - if someone already looked up a location at 4:30 in this video and another user clicks at 4:32, it's the same scene. Return the cached result instantly.
- **By video** - if I've already gathered channel context and video metadata for this video, I don't need to do it again for a different frame in the same video.
- **Cache invalidation** - results should probably expire after some period (weeks/months) so they can benefit from model improvements. But there's no rush on this for MVP.

Caching doesn't just save costs - it creates a network effect. Once one person runs a Full Video Scan on a popular travel video, every future viewer gets the full location map instantly. Popular videos become "pre-mapped" by early users. Over time, the most-watched travel and drone content on YouTube is already mapped before anyone even clicks the button. The more people use GeoLens, the more videos are pre-mapped, the more instant the experience becomes for everyone. That's a flywheel that compounds.

### Key Validation Questions

After launching the MVP, I need answers to:

- Do people install and use the extension?
- How often do they click "Find Location"?
- Do they come back after their first session? After a week?
- What types of videos do they use it on most? (travel, drone, documentary, other?)
- Do they hit the 5/day limit and want more?
- When the result is wrong, do they bounce or try again with a different frame?
- What accuracy rate keeps people coming back?
- Are they telling other people about it?

---

## 15. Technical Approach (High Level)

This section describes the architectural direction, not specific libraries or frameworks. The implementation session should pick the right tools - but this is the shape I'm thinking.

### Core Architecture: Agent Harness

The backend should be built as an **AI agent harness** - similar in spirit to how Claude Code works. Not a single API call to an AI model, but an orchestrated system where multiple agents work together, each with access to tools, and a coordinator that synthesizes their findings.

Think of it like a team of investigators, not a single oracle.

### Multi-Agent Pipeline

The geolocation task naturally decomposes into multiple independent evidence-gathering steps. I want a multi-agent system where:

- **A frame analysis agent** examines the captured video frame - terrain, vegetation, architecture, signage, road markings, sun angle, weather, infrastructure style, any visible text or scripts
- **A metadata agent** extracts and reasons about the video's title, description, tags, upload date, and any location hints in the text
- **A channel context agent** looks at the creator's channel - what country/region do they usually film in? What are their recent videos about? Do they have a pattern?
- **A comments agent** reads through the video's comments looking for location mentions, place names, user corrections, or direct answers. Comments often literally contain the answer - someone writes "the waterfall at 12:30 is Ravana Falls!" and that's the highest-confidence signal in the entire pipeline. This agent is especially powerful for popular videos with active comment sections.
- **A web research agent** can search the web for related information - the video title, the creator's known filming locations, similar content from other creators
- **A synthesis agent** takes all the evidence gathered by the other agents and triangulates to a final location with a confidence score and evidence chain

Each agent operates somewhat independently, gathering its own type of evidence. The synthesis agent is the one that combines weak signals into a strong conclusion.

### Tool Orchestration

Agents need tools. The system should support agents calling external tools as part of their reasoning:

- **Vision/image analysis** - analyze the frame for visual clues
- **Web search** - search for contextual information
- **Map/geocoding APIs** - convert place names to coordinates, look up geographic data
- **Reverse image search** - check if this exact scene appears elsewhere online
- **YouTube data access** - pull video metadata, channel info, related videos
- **Text/OCR extraction** - read text visible in the frame

The agent harness should make it easy to add new tools over time as I discover which evidence signals are most valuable.

### Multi-Provider Support

I don't want to be locked into a single AI provider. The system should support multiple LLM providers:

- Different agents might work best with different models (a vision-specialized model for frame analysis, a reasoning-heavy model for synthesis)
- If one provider has an outage or rate limit, the system can fall back
- As new models come out, I want to be able to swap them in without rewriting the pipeline
- Cost optimization - some agents might use cheaper models for simpler tasks, more expensive ones for the critical synthesis step

### Long-Running Task Support

This is not a "send one request, get one response" system. A full geolocation pipeline involves:

- Multiple agents running (some in parallel, some sequential)
- External tool calls (web searches, API lookups)
- Potentially multiple rounds of reasoning if initial evidence is inconclusive

A single lookup could take 15-30 seconds and involve 5-10+ agent steps. The system needs to handle this as a long-running task with:

- Async processing (the Chrome extension sends a request and polls or subscribes for the result)
- Progress updates (so the UI can show "analyzing frame..." → "checking channel history..." → "triangulating location...")
- Timeout handling (return the best partial result if the full pipeline takes too long)
- Error resilience (if one agent fails, the others should still contribute their findings)

### Open Source Foundation

I want to build on an established open-source multi-agent / tool orchestration framework rather than writing agent infrastructure from scratch. The ecosystem has mature options for:

- Agent orchestration and multi-step workflows
- Tool registration and execution
- Multi-provider LLM integration
- Structured output and result parsing
- Conversation/context management

The implementation session should evaluate what's available and pick the best fit. The key criteria: mature, well-maintained, supports multi-agent workflows with tool use, supports multiple LLM providers, and doesn't lock me into a specific model vendor.

### The Pipeline Flow

At a high level, when a user clicks "Find Location":

```
1. Chrome extension captures frame + video page context
2. Sends to backend API
3. Backend creates a geolocation task
4. Agent harness spins up the pipeline:
   ├── Frame Analysis Agent (vision) ──────────┐
   ├── Metadata Agent (text reasoning) ─────────┤
   ├── Channel Context Agent (web/API) ─────────┤
   ├── Comments Agent (read video comments) ────┤  → Synthesis Agent → Result
   ├── Web Research Agent (search) ─────────────┤
   └── (optional) Related Content Agent ────────┘
5. Synthesis agent combines all evidence
6. Backend returns: location, coordinates, confidence, evidence chain
7. Chrome extension displays the result inline
```

Some agents can run in parallel (frame analysis and metadata extraction don't depend on each other). Some might run sequentially (web research might use clues from frame analysis to know what to search for). The orchestrator handles this.

### Model Evaluation Needed

Before building the pipeline, I need to do a proper analysis of what's available in the AI model landscape. This is a critical pre-build step because the cost and capability of the models I choose directly affect whether the unit economics work and whether the output is good enough.

Things I need to evaluate:

- **Vision/multimodal models** - which models are best at analyzing a photo and reasoning about geographic clues (terrain, architecture, vegetation, signage, scripts)? How do they compare on accuracy vs. cost vs. latency? Some models might be great at landmark recognition but weak at reasoning about subtle environmental clues. I need to test this on real video frames, not just benchmarks.
- **Reasoning/text models** - which models are best at the synthesis step (taking multiple evidence signals and triangulating to a location)? This is a reasoning-heavy task, not just retrieval.
- **Cost per lookup** - a single lookup runs multiple agents. If each agent call costs $0.01-0.05, a full pipeline might cost $0.05-0.25 per lookup. I need to model this out and figure out if the unit economics work at 5 free lookups/day and a $8-15/month pro tier.
- **Cheaper models for simpler tasks** - not every agent needs the most expensive model. The metadata extraction agent might work fine with a smaller, cheaper model. The frame analysis and synthesis agents probably need something more capable. I should tier my model usage by task complexity.
- **Open-source vs. proprietary** - are there open-source vision models that can run locally or on cheaper infrastructure and still give acceptable results? This could dramatically change the cost picture.
- **Specialized geolocation models** - are there models or fine-tunes specifically trained for geolocation tasks? The GeoGuessr community and OSINT world may have produced something useful.
- **Latency tradeoffs** - faster models that are slightly less accurate might be better for the MVP than slower, more accurate ones. I need to find the right balance for a 15-30 second total pipeline time.

This evaluation should happen early - before I commit to a pipeline architecture - because the results might change which agents I need, how many steps the pipeline has, and whether certain evidence signals are worth the cost of gathering them.

The core design principle here: **models should be swappable at every level of the pipeline.** I don't want to be in a position where switching from one vision model to another requires rewriting agent logic. The model should be a configuration choice, not a hardcoded dependency. New models come out constantly - I need to be able to drop in a better or cheaper model the day it's available and see immediate improvement.

### What I'm NOT Specifying

- Specific AI models or providers to use
- Specific open-source framework to build on
- Database choice or data model
- Hosting/deployment infrastructure
- Programming language (though the agent ecosystem is strongest in Python and TypeScript)
- Specific APIs for maps, search, or YouTube data

These choices should be made during implementation based on what works best in practice.

---

## 16. Brand and Messaging

### I want to frame it as:
> "Discover where any YouTube scene was filmed."

### I want to avoid framing it as:
> "AI that gives exact GPS coordinates."

**My reasoning:** The first framing aligns with what users actually want (satisfying curiosity), is easier to deliver on, and gives me room to improve accuracy over time. The second framing sets unrealistic precision expectations.

### My philosophy
I want to optimize for satisfying curiosity with a trustworthy, explainable answer - not for generating precise coordinates. This positions the product as "an AI that helps people understand the world" rather than "an AI that guesses locations."

---

## 17. Success Metrics

### What success looks like to me:
Users consistently feeling: "I finally found where this was filmed."

### Metrics I want to track:
- Daily/weekly active users
- Lookups per user per session
- Return rate (7-day, 30-day)
- User-confirmed accuracy rate
- Free-to-paid conversion rate
- Net promoter score
- Shared discoveries per user
- Hot searches engagement
- API request volume (if/when I launch the API)

---

## 18. Product Evolution Roadmap (High Level)

This is how I see the product evolving, roughly in order:

1. **Chrome extension MVP** - Quick Lookup mode on YouTube, single-frame lookup, basic results panel
2. **Full Video Scan** - Analyze the entire video, produce a complete location map with timestamps. This is the virality driver.
3. **Inline YouTube integration** - Injected timeline markers, location cards, polished visual experience
4. **History** - Save and browse past discoveries, personal discovery map
5. **Sharing** - Shareable location cards and discovery links
6. **Pro tier** - Unlimited lookups, detailed evidence, export features
7. **Community layer** - Hot searches, trending discoveries, crowdsourced accuracy
8. **API** - Open the inference engine to other products
9. **Creator tools** - Auto-generate location lists for video creators
10. **Mobile app** - Take the experience beyond the browser
11. **AI integrations** - ChatGPT plugin, Claude integration
12. **Affiliate layer** - Hotels, tours, attractions for identified locations
13. **Enterprise** - Tailored offerings for journalism, OSINT, research

---

## 19. Long-Term Vision

The Chrome extension is my first interface. My broader vision is that GeoLens becomes the default answer whenever someone asks "Where was this filmed?" - analogous to how Google became the default for "What is this?"

Over time, GeoLens becomes three things:

1. **A tool** - the best way to identify where a video was filmed
2. **A platform** - a growing, shared library of location discoveries
3. **An engine** - the underlying AI that any product can call via API

The extension is just one client of that engine. The community's discoveries become a dataset that makes the engine better. The engine powers the tool and the platform. Everything reinforces everything else.

---

## 20. Analogies and Mental Models

- **Google answers "What is this?"** - I want GeoLens to answer "Where is this?"
- **Shazam for locations** - hear a song, Shazam identifies it; see a place, GeoLens identifies it
- **GeoGuessr as validation** - proves people enjoy and are skilled at location discovery; I want to automate and extend this
- **SponsorBlock as UX precedent** - a Chrome extension that injects UI into YouTube's timeline. Proves that timeline-integrated extensions can feel native and gain massive adoption.

---

## 21. Risks and Open Questions

| Area | Risk or Question |
|---|---|
| Accuracy | How accurate can AI geolocation be for non-landmark locations? |
| Unit economics | What does a single lookup cost in AI API calls? Does the math work at scale? |
| User expectations | Will users accept probabilistic answers or expect GPS precision? |
| Competition | Could Google, YouTube, or other large platforms build this natively? |
| Platform policies | Are there restrictions on Chrome extensions that inject UI into YouTube? |
| Data sources | What contextual data is reliably available and accessible from the YouTube page? |
| Privacy | Any concerns with capturing and processing video frames? What data do I store? |
| Scaling | How does the AI pipeline need to evolve as usage grows? |
| Edge cases | How well does the system handle non-location content (gaming, tutorials, talking heads)? |
| Caching | How aggressively can I cache without serving stale results? |
| Auth | What's the right auth approach for rate limiting and history without adding too much friction? |
| Community | Will users actually engage with sharing and hot searches, or just use it as a tool? |
| Moderation | If there's a community layer, what moderation is needed? |
| Multi-platform | When and how should I expand beyond YouTube? What changes are needed? |

---

## 22. What This Document Does NOT Cover

This document includes high-level technical direction (Section 15) but intentionally omits:

- Specific AI models, providers, or framework choices
- Database schemas or data models
- Detailed implementation plans or task breakdowns
- Code structure or repository organization
- Hosting, deployment, or infrastructure decisions
- Specific third-party service choices
- API contracts or interface definitions

I want to figure these out during implementation through discussion and iteration.

---

*This document captures my product idea, the problem space, target users, business model options, and vision for GeoLens. I'll use it as a starting point for building.*
