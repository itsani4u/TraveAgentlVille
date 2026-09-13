# Prompt Comparison Table

| Prompt | Purpose | Temperature | Output Format | Key risk it guards against |
|---|---|---|---|---|
| `ITINERARY_AGENT_SYSTEM_PROMPT` | Draft a full multi-day itinerary | 0.1 | Strict JSON (`TravelPlan`) | Budget overrun, uneven day-to-day activity counts |
| `ACTIVITY_AND_WEATHER_ARE_COMPATIBLE_SYSTEM_PROMPT` | Judge one activity against one day's weather | 0.1 | Strict JSON (`is_compatible`, `justification`) | Scheduling a hike during a storm |
| `REACT_REVISION_AGENT_SYSTEM_PROMPT` | Drive the THOUGHT/ACTION loop that fixes the draft | 0.1 | `THOUGHT:` + `ACTION: {json}` per turn | Agent looping forever, or finalizing an invalid plan |
| `NARRATIVE_SUMMARY_SYSTEM_PROMPT` | Turn the final JSON into prose | 0.5 | Free-form prose | Sounding like a JSON dump instead of a travel writer |

## Why low temperature for structured stages
Anything that has to parse into a Pydantic model (`TravelPlan`,
`CompatibilityResult`, `ACTION` JSON) uses temperature 0.0-0.2 per NFR-3, so
formatting stays consistent run over run. The narrative stage is the only
place we loosen that, since some stylistic variety there is a feature, not
a bug.

## Why one prompt per responsibility
Each prompt does exactly one job. This keeps the JSON schema each prompt
must produce small and easy for a smaller/cheaper Gemini model to hit
reliably, versus one giant "do everything" prompt.
