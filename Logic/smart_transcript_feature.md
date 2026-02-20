# Smart Transcript Feature Logic

This feature combines ASR (Speech-to-Text) and Speaker Diarization to produce a punctuated, speaker-attributed transcript.

## Algorithm: Punctuation & Speaker Alignment

### 1. Punctuation Alignment (Character Lookahead)
Since word-level timestamps provided by the ASR model are often unpunctuated, we align them with the full punctuated transcript using a character-by-character lookahead.

- **Input**: `timedWords` (list of words with start/end times), `fullText` (punctuated string).
- **Process**:
    1. Iterate through `timedWords`.
    2. For each word, find its starting position in `fullText` after the previous match.
    3. Capture all characters following the word until the start of the next timed word's characters.
    4. Store these captured characters as the word's "suffix" (containing spaces and punctuation).
- **Benefit**: Avoids the "Tokenization Mismatch" problem where array-indexing fails when punctuation is attached to words.

### 2. Speaker Attribution (Midpoint Collision)
We map punctuated words to speakers using the segments returned by the Diarization engine.

- **Process**:
    1. For each `punctuatedWord`, calculate its `midpoint = (start + end) / 2`.
    2. Locate the Diarization segment that contains this `midpoint`.
    3. Group words into contiguous "speaker turns" until the speaker ID changes.

### 3. Rendering (Interactive Chat View)
The final result is rendered as a series of chat bubbles:
- **Header**: Speaker ID and duration range.
- **Body**: Corrected, punctuated text.
- **Interactivity**: Clicking any sentence jumps the global audio preview player to that timestamp.

## Files Involved
- [ui-analysis.js](file:///home/user/voice-clone/qwen_tts_service/ui/js/ui-analysis.js): Core logic for alignment and rendering.
- [index.html](file:///home/user/voice-clone/qwen_tts_service/ui/index.html): UI layout for the new tab.
- [ui-core.js](file:///home/user/voice-clone/qwen_tts_service/ui/js/ui-core.js): Global state for analysis results.
