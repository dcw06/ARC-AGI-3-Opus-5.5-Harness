#!/usr/bin/env python3
"""Reconstruct the recorded continuation scorecard without model/network calls.

Data are a transcription of source_url, not raw inference or engine evidence.
Completion flags follow each game's displayed sequential completed-level count.
This script cannot verify policy bindings, checkpoint restoration, or run costs.
"""
import json
import math

DATA = json.loads(r'''{
  "source_url": "https://arcprize.org/scorecards/82bd80c9-3b07-43e7-9c11-f7aff912dd35",
  "accessed": "2026-11-20",
  "evidence_type": "Public scorecard transcription; replay-of-recorded-actions; execution lineage not verified",
  "tags": [
    "claude-arc-v1",
    "hypotheses",
    "competition",
    "replay-of-recorded-actions",
    "baseline-continue-v1",
    "agent"
  ],
  "games": [
    {
      "game_id": "ar25-0c556536",
      "score_display": "100.00",
      "completed": 8,
      "total_levels": 8,
      "state": "WIN",
      "actions": 393,
      "resets": 0,
      "replay_url": "https://arcprize.org/replay/73a60053-b6f9-4027-8000-62b0afa6a3cb",
      "recording_url": "https://arcprize.org/api/recordings/ar25-0c556536/73a60053-b6f9-4027-8000-62b0afa6a3cb",
      "levels": [
        {
          "level": 1,
          "score_display": "115.00",
          "actions": 17,
          "human_baseline": 32,
          "completed": true
        },
        {
          "level": 2,
          "score_display": "115.00",
          "actions": 14,
          "human_baseline": 50,
          "completed": true
        },
        {
          "level": 3,
          "score_display": "115.00",
          "actions": 41,
          "human_baseline": 75,
          "completed": true
        },
        {
          "level": 4,
          "score_display": "81.44",
          "actions": 41,
          "human_baseline": 37,
          "completed": true
        },
        {
          "level": 5,
          "score_display": "115.00",
          "actions": 28,
          "human_baseline": 89,
          "completed": true
        },
        {
          "level": 6,
          "score_display": "115.00",
          "actions": 115,
          "human_baseline": 159,
          "completed": true
        },
        {
          "level": 7,
          "score_display": "115.00",
          "actions": 56,
          "human_baseline": 233,
          "completed": true
        },
        {
          "level": 8,
          "score_display": "81.22",
          "actions": 81,
          "human_baseline": 73,
          "completed": true
        }
      ]
    },
    {
      "game_id": "bp35-0a0ad940",
      "score_display": "3.63",
      "completed": 4,
      "total_levels": 9,
      "state": "GAME_OVER",
      "actions": 700,
      "resets": 22,
      "replay_url": "https://arcprize.org/replay/ac6b3c5e-4580-466b-9a35-cad90ab40d5e",
      "recording_url": "https://arcprize.org/api/recordings/bp35-0a0ad940/ac6b3c5e-4580-466b-9a35-cad90ab40d5e",
      "levels": [
        {
          "level": 1,
          "score_display": "115.00",
          "actions": 17,
          "human_baseline": 21,
          "completed": true
        },
        {
          "level": 2,
          "score_display": "5.59",
          "actions": 203,
          "human_baseline": 48,
          "completed": true
        },
        {
          "level": 3,
          "score_display": "10.31",
          "actions": 137,
          "human_baseline": 44,
          "completed": true
        },
        {
          "level": 4,
          "score_display": "1.55",
          "actions": 305,
          "human_baseline": 38,
          "completed": true
        },
        {
          "level": 5,
          "score_display": "0.00",
          "actions": 38,
          "human_baseline": 33,
          "completed": false
        },
        {
          "level": 6,
          "score_display": "0.00",
          "actions": 0,
          "human_baseline": 87,
          "completed": false
        },
        {
          "level": 7,
          "score_display": "0.00",
          "actions": 0,
          "human_baseline": 86,
          "completed": false
        },
        {
          "level": 8,
          "score_display": "0.00",
          "actions": 0,
          "human_baseline": 131,
          "completed": false
        },
        {
          "level": 9,
          "score_display": "0.00",
          "actions": 0,
          "human_baseline": 163,
          "completed": false
        }
      ]
    },
    {
      "game_id": "cd82-fb555c5d",
      "score_display": "14.29",
      "completed": 2,
      "total_levels": 6,
      "state": "GAME_OVER",
      "actions": 200,
      "resets": 1,
      "replay_url": "https://arcprize.org/replay/77e950c3-d26d-4388-bd9d-b3fea296b50e",
      "recording_url": "https://arcprize.org/api/recordings/cd82-fb555c5d/77e950c3-d26d-4388-bd9d-b3fea296b50e",
      "levels": [
        {
          "level": 1,
          "score_display": "115.00",
          "actions": 28,
          "human_baseline": 55,
          "completed": true
        },
        {
          "level": 2,
          "score_display": "115.00",
          "actions": 7,
          "human_baseline": 8,
          "completed": true
        },
        {
          "level": 3,
          "score_display": "0.00",
          "actions": 165,
          "human_baseline": 41,
          "completed": false
        },
        {
          "level": 4,
          "score_display": "0.00",
          "actions": 0,
          "human_baseline": 21,
          "completed": false
        },
        {
          "level": 5,
          "score_display": "0.00",
          "actions": 0,
          "human_baseline": 23,
          "completed": false
        },
        {
          "level": 6,
          "score_display": "0.00",
          "actions": 0,
          "human_baseline": 23,
          "completed": false
        }
      ]
    },
    {
      "game_id": "cn04-2fe56bfb",
      "score_display": "47.62",
      "completed": 4,
      "total_levels": 6,
      "state": "GAME_OVER",
      "actions": 800,
      "resets": 4,
      "replay_url": "https://arcprize.org/replay/5ae76259-5b6c-4453-848d-69c742c0e469",
      "recording_url": "https://arcprize.org/api/recordings/cn04-2fe56bfb/5ae76259-5b6c-4453-848d-69c742c0e469",
      "levels": [
        {
          "level": 1,
          "score_display": "115.00",
          "actions": 19,
          "human_baseline": 29,
          "completed": true
        },
        {
          "level": 2,
          "score_display": "115.00",
          "actions": 33,
          "human_baseline": 54,
          "completed": true
        },
        {
          "level": 3,
          "score_display": "115.00",
          "actions": 50,
          "human_baseline": 85,
          "completed": true
        },
        {
          "level": 4,
          "score_display": "115.00",
          "actions": 203,
          "human_baseline": 300,
          "completed": true
        },
        {
          "level": 5,
          "score_display": "0.00",
          "actions": 495,
          "human_baseline": 208,
          "completed": false
        },
        {
          "level": 6,
          "score_display": "0.00",
          "actions": 0,
          "human_baseline": 113,
          "completed": false
        }
      ]
    },
    {
      "game_id": "dc22-fdcac232",
      "score_display": "40.34",
      "completed": 4,
      "total_levels": 6,
      "state": "GAME_OVER",
      "actions": 1250,
      "resets": 4,
      "replay_url": "https://arcprize.org/replay/90aae319-174f-4414-a0d6-92085daefebc",
      "recording_url": "https://arcprize.org/api/recordings/dc22-fdcac232/90aae319-174f-4414-a0d6-92085daefebc",
      "levels": [
        {
          "level": 1,
          "score_display": "115.00",
          "actions": 32,
          "human_baseline": 59,
          "completed": true
        },
        {
          "level": 2,
          "score_display": "66.59",
          "actions": 125,
          "human_baseline": 102,
          "completed": true
        },
        {
          "level": 3,
          "score_display": "115.00",
          "actions": 59,
          "human_baseline": 67,
          "completed": true
        },
        {
          "level": 4,
          "score_display": "63.48",
          "actions": 123,
          "human_baseline": 98,
          "completed": true
        },
        {
          "level": 5,
          "score_display": "0.00",
          "actions": 911,
          "human_baseline": 324,
          "completed": false
        },
        {
          "level": 6,
          "score_display": "0.00",
          "actions": 0,
          "human_baseline": 578,
          "completed": false
        }
      ]
    },
    {
      "game_id": "ft09-0d8bbf25",
      "score_display": "100.00",
      "completed": 6,
      "total_levels": 6,
      "state": "WIN",
      "actions": 75,
      "resets": 0,
      "replay_url": "https://arcprize.org/replay/2b65071d-774c-41b8-aab5-69b03693bce8",
      "recording_url": "https://arcprize.org/api/recordings/ft09-0d8bbf25/2b65071d-774c-41b8-aab5-69b03693bce8",
      "levels": [
        {
          "level": 1,
          "score_display": "115.00",
          "actions": 4,
          "human_baseline": 43,
          "completed": true
        },
        {
          "level": 2,
          "score_display": "115.00",
          "actions": 7,
          "human_baseline": 12,
          "completed": true
        },
        {
          "level": 3,
          "score_display": "115.00",
          "actions": 14,
          "human_baseline": 23,
          "completed": true
        },
        {
          "level": 4,
          "score_display": "115.00",
          "actions": 16,
          "human_baseline": 28,
          "completed": true
        },
        {
          "level": 5,
          "score_display": "115.00",
          "actions": 21,
          "human_baseline": 65,
          "completed": true
        },
        {
          "level": 6,
          "score_display": "115.00",
          "actions": 13,
          "human_baseline": 37,
          "completed": true
        }
      ]
    },
    {
      "game_id": "g50t-5849a774",
      "score_display": "10.71",
      "completed": 2,
      "total_levels": 7,
      "state": "GAME_OVER",
      "actions": 900,
      "resets": 6,
      "replay_url": "https://arcprize.org/replay/154c56c9-627e-468b-abb5-0045ee0f7325",
      "recording_url": "https://arcprize.org/api/recordings/g50t-5849a774/154c56c9-627e-468b-abb5-0045ee0f7325",
      "levels": [
        {
          "level": 1,
          "score_display": "115.00",
          "actions": 39,
          "human_baseline": 78,
          "completed": true
        },
        {
          "level": 2,
          "score_display": "115.00",
          "actions": 122,
          "human_baseline": 175,
          "completed": true
        },
        {
          "level": 3,
          "score_display": "0.00",
          "actions": 739,
          "human_baseline": 179,
          "completed": false
        },
        {
          "level": 4,
          "score_display": "0.00",
          "actions": 0,
          "human_baseline": 230,
          "completed": false
        },
        {
          "level": 5,
          "score_display": "0.00",
          "actions": 0,
          "human_baseline": 96,
          "completed": false
        },
        {
          "level": 6,
          "score_display": "0.00",
          "actions": 0,
          "human_baseline": 54,
          "completed": false
        },
        {
          "level": 7,
          "score_display": "0.00",
          "actions": 0,
          "human_baseline": 67,
          "completed": false
        }
      ]
    },
    {
      "game_id": "ka59-38d34dbb",
      "score_display": "10.16",
      "completed": 3,
      "total_levels": 7,
      "state": "GAME_OVER",
      "actions": 750,
      "resets": 4,
      "replay_url": "https://arcprize.org/replay/38302e66-037c-4630-8fa4-d1bbd6f9284a",
      "recording_url": "https://arcprize.org/api/recordings/ka59-38d34dbb/38302e66-037c-4630-8fa4-d1bbd6f9284a",
      "levels": [
        {
          "level": 1,
          "score_display": "87.11",
          "actions": 30,
          "human_baseline": 28,
          "completed": true
        },
        {
          "level": 2,
          "score_display": "32.91",
          "actions": 190,
          "human_baseline": 109,
          "completed": true
        },
        {
          "level": 3,
          "score_display": "43.87",
          "actions": 77,
          "human_baseline": 51,
          "completed": true
        },
        {
          "level": 4,
          "score_display": "0.00",
          "actions": 453,
          "human_baseline": 51,
          "completed": false
        },
        {
          "level": 5,
          "score_display": "0.00",
          "actions": 0,
          "human_baseline": 33,
          "completed": false
        },
        {
          "level": 6,
          "score_display": "0.00",
          "actions": 0,
          "human_baseline": 132,
          "completed": false
        },
        {
          "level": 7,
          "score_display": "0.00",
          "actions": 0,
          "human_baseline": 326,
          "completed": false
        }
      ]
    },
    {
      "game_id": "lf52-271a04aa",
      "score_display": "8.54",
      "completed": 4,
      "total_levels": 10,
      "state": "GAME_OVER",
      "actions": 1350,
      "resets": 3,
      "replay_url": "https://arcprize.org/replay/56ecf233-2da2-4f1e-8d8f-846b9c4bf39f",
      "recording_url": "https://arcprize.org/api/recordings/lf52-271a04aa/56ecf233-2da2-4f1e-8d8f-846b9c4bf39f",
      "levels": [
        {
          "level": 1,
          "score_display": "115.00",
          "actions": 8,
          "human_baseline": 32,
          "completed": true
        },
        {
          "level": 2,
          "score_display": "1.30",
          "actions": 710,
          "human_baseline": 81,
          "completed": true
        },
        {
          "level": 3,
          "score_display": "115.00",
          "actions": 49,
          "human_baseline": 60,
          "completed": true
        },
        {
          "level": 4,
          "score_display": "1.75",
          "actions": 537,
          "human_baseline": 71,
          "completed": true
        },
        {
          "level": 5,
          "score_display": "0.00",
          "actions": 46,
          "human_baseline": 205,
          "completed": false
        },
        {
          "level": 6,
          "score_display": "0.00",
          "actions": 0,
          "human_baseline": 148,
          "completed": false
        },
        {
          "level": 7,
          "score_display": "0.00",
          "actions": 0,
          "human_baseline": 244,
          "completed": false
        },
        {
          "level": 8,
          "score_display": "0.00",
          "actions": 0,
          "human_baseline": 109,
          "completed": false
        },
        {
          "level": 9,
          "score_display": "0.00",
          "actions": 0,
          "human_baseline": 164,
          "completed": false
        },
        {
          "level": 10,
          "score_display": "0.00",
          "actions": 0,
          "human_baseline": 225,
          "completed": false
        }
      ]
    },
    {
      "game_id": "lp85-305b61c3",
      "score_display": "100.00",
      "completed": 8,
      "total_levels": 8,
      "state": "WIN",
      "actions": 124,
      "resets": 0,
      "replay_url": "https://arcprize.org/replay/f7edf02a-bbe3-45f4-b28c-3f159571ca36",
      "recording_url": "https://arcprize.org/api/recordings/lp85-305b61c3/f7edf02a-bbe3-45f4-b28c-3f159571ca36",
      "levels": [
        {
          "level": 1,
          "score_display": "115.00",
          "actions": 7,
          "human_baseline": 17,
          "completed": true
        },
        {
          "level": 2,
          "score_display": "115.00",
          "actions": 10,
          "human_baseline": 38,
          "completed": true
        },
        {
          "level": 3,
          "score_display": "115.00",
          "actions": 16,
          "human_baseline": 31,
          "completed": true
        },
        {
          "level": 4,
          "score_display": "88.58",
          "actions": 17,
          "human_baseline": 16,
          "completed": true
        },
        {
          "level": 5,
          "score_display": "115.00",
          "actions": 18,
          "human_baseline": 41,
          "completed": true
        },
        {
          "level": 6,
          "score_display": "115.00",
          "actions": 24,
          "human_baseline": 60,
          "completed": true
        },
        {
          "level": 7,
          "score_display": "115.00",
          "actions": 8,
          "human_baseline": 26,
          "completed": true
        },
        {
          "level": 8,
          "score_display": "115.00",
          "actions": 24,
          "human_baseline": 159,
          "completed": true
        }
      ]
    },
    {
      "game_id": "ls20-9607627b",
      "score_display": "10.71",
      "completed": 2,
      "total_levels": 7,
      "state": "GAME_OVER",
      "actions": 800,
      "resets": 6,
      "replay_url": "https://arcprize.org/replay/1cb6a0f9-ded4-42f9-b226-e703a078ceaf",
      "recording_url": "https://arcprize.org/api/recordings/ls20-9607627b/1cb6a0f9-ded4-42f9-b226-e703a078ceaf",
      "levels": [
        {
          "level": 1,
          "score_display": "115.00",
          "actions": 15,
          "human_baseline": 22,
          "completed": true
        },
        {
          "level": 2,
          "score_display": "115.00",
          "actions": 45,
          "human_baseline": 123,
          "completed": true
        },
        {
          "level": 3,
          "score_display": "0.00",
          "actions": 740,
          "human_baseline": 73,
          "completed": false
        },
        {
          "level": 4,
          "score_display": "0.00",
          "actions": 0,
          "human_baseline": 84,
          "completed": false
        },
        {
          "level": 5,
          "score_display": "0.00",
          "actions": 0,
          "human_baseline": 96,
          "completed": false
        },
        {
          "level": 6,
          "score_display": "0.00",
          "actions": 0,
          "human_baseline": 192,
          "completed": false
        },
        {
          "level": 7,
          "score_display": "0.00",
          "actions": 0,
          "human_baseline": 186,
          "completed": false
        }
      ]
    },
    {
      "game_id": "m0r0-492f87ba",
      "score_display": "14.29",
      "completed": 2,
      "total_levels": 6,
      "state": "GAME_OVER",
      "actions": 1150,
      "resets": 7,
      "replay_url": "https://arcprize.org/replay/ef1284a7-d197-4c0e-a1a8-3c12a0f764e2",
      "recording_url": "https://arcprize.org/api/recordings/m0r0-492f87ba/ef1284a7-d197-4c0e-a1a8-3c12a0f764e2",
      "levels": [
        {
          "level": 1,
          "score_display": "115.00",
          "actions": 15,
          "human_baseline": 30,
          "completed": true
        },
        {
          "level": 2,
          "score_display": "115.00",
          "actions": 56,
          "human_baseline": 111,
          "completed": true
        },
        {
          "level": 3,
          "score_display": "0.00",
          "actions": 1079,
          "human_baseline": 203,
          "completed": false
        },
        {
          "level": 4,
          "score_display": "0.00",
          "actions": 0,
          "human_baseline": 26,
          "completed": false
        },
        {
          "level": 5,
          "score_display": "0.00",
          "actions": 0,
          "human_baseline": 500,
          "completed": false
        },
        {
          "level": 6,
          "score_display": "0.00",
          "actions": 0,
          "human_baseline": 237,
          "completed": false
        }
      ]
    },
    {
      "game_id": "r11l-495a7899",
      "score_display": "92.35",
      "completed": 6,
      "total_levels": 6,
      "state": "WIN",
      "actions": 159,
      "resets": 1,
      "replay_url": "https://arcprize.org/replay/5afead42-4b2f-46b9-a0dc-c3ed70e29d69",
      "recording_url": "https://arcprize.org/api/recordings/r11l-495a7899/5afead42-4b2f-46b9-a0dc-c3ed70e29d69",
      "levels": [
        {
          "level": 1,
          "score_display": "115.00",
          "actions": 4,
          "human_baseline": 22,
          "completed": true
        },
        {
          "level": 2,
          "score_display": "115.00",
          "actions": 11,
          "human_baseline": 33,
          "completed": true
        },
        {
          "level": 3,
          "score_display": "115.00",
          "actions": 17,
          "human_baseline": 51,
          "completed": true
        },
        {
          "level": 4,
          "score_display": "115.00",
          "actions": 15,
          "human_baseline": 26,
          "completed": true
        },
        {
          "level": 5,
          "score_display": "115.00",
          "actions": 30,
          "human_baseline": 52,
          "completed": true
        },
        {
          "level": 6,
          "score_display": "35.71",
          "actions": 82,
          "human_baseline": 49,
          "completed": true
        }
      ]
    },
    {
      "game_id": "re86-8af5384d",
      "score_display": "58.33",
      "completed": 6,
      "total_levels": 8,
      "state": "GAME_OVER",
      "actions": 1300,
      "resets": 3,
      "replay_url": "https://arcprize.org/replay/b68a95d7-75cb-4293-9044-a43307858c10",
      "recording_url": "https://arcprize.org/api/recordings/re86-8af5384d/b68a95d7-75cb-4293-9044-a43307858c10",
      "levels": [
        {
          "level": 1,
          "score_display": "115.00",
          "actions": 20,
          "human_baseline": 26,
          "completed": true
        },
        {
          "level": 2,
          "score_display": "115.00",
          "actions": 36,
          "human_baseline": 42,
          "completed": true
        },
        {
          "level": 3,
          "score_display": "115.00",
          "actions": 47,
          "human_baseline": 86,
          "completed": true
        },
        {
          "level": 4,
          "score_display": "115.00",
          "actions": 42,
          "human_baseline": 108,
          "completed": true
        },
        {
          "level": 5,
          "score_display": "115.00",
          "actions": 151,
          "human_baseline": 189,
          "completed": true
        },
        {
          "level": 6,
          "score_display": "115.00",
          "actions": 77,
          "human_baseline": 139,
          "completed": true
        },
        {
          "level": 7,
          "score_display": "0.00",
          "actions": 927,
          "human_baseline": 424,
          "completed": false
        },
        {
          "level": 8,
          "score_display": "0.00",
          "actions": 0,
          "human_baseline": 241,
          "completed": false
        }
      ]
    },
    {
      "game_id": "s5i5-18d95033",
      "score_display": "85.34",
      "completed": 8,
      "total_levels": 8,
      "state": "WIN",
      "actions": 486,
      "resets": 0,
      "replay_url": "https://arcprize.org/replay/a538f2f2-43f3-425f-a4c5-9ccb0910beb5",
      "recording_url": "https://arcprize.org/api/recordings/s5i5-18d95033/a538f2f2-43f3-425f-a4c5-9ccb0910beb5",
      "levels": [
        {
          "level": 1,
          "score_display": "115.00",
          "actions": 13,
          "human_baseline": 20,
          "completed": true
        },
        {
          "level": 2,
          "score_display": "115.00",
          "actions": 28,
          "human_baseline": 89,
          "completed": true
        },
        {
          "level": 3,
          "score_display": "115.00",
          "actions": 80,
          "human_baseline": 106,
          "completed": true
        },
        {
          "level": 4,
          "score_display": "115.00",
          "actions": 31,
          "human_baseline": 54,
          "completed": true
        },
        {
          "level": 5,
          "score_display": "115.00",
          "actions": 28,
          "human_baseline": 162,
          "completed": true
        },
        {
          "level": 6,
          "score_display": "111.42",
          "actions": 36,
          "human_baseline": 38,
          "completed": true
        },
        {
          "level": 7,
          "score_display": "68.38",
          "actions": 104,
          "human_baseline": 86,
          "completed": true
        },
        {
          "level": 8,
          "score_display": "25.00",
          "actions": 166,
          "human_baseline": 83,
          "completed": true
        }
      ]
    },
    {
      "game_id": "sb26-7fbdac44",
      "score_display": "100.00",
      "completed": 8,
      "total_levels": 8,
      "state": "WIN",
      "actions": 127,
      "resets": 0,
      "replay_url": "https://arcprize.org/replay/9708ab89-a4d1-400c-b0fe-0e2302541830",
      "recording_url": "https://arcprize.org/api/recordings/sb26-7fbdac44/9708ab89-a4d1-400c-b0fe-0e2302541830",
      "levels": [
        {
          "level": 1,
          "score_display": "115.00",
          "actions": 9,
          "human_baseline": 18,
          "completed": true
        },
        {
          "level": 2,
          "score_display": "115.00",
          "actions": 15,
          "human_baseline": 28,
          "completed": true
        },
        {
          "level": 3,
          "score_display": "115.00",
          "actions": 16,
          "human_baseline": 18,
          "completed": true
        },
        {
          "level": 4,
          "score_display": "115.00",
          "actions": 15,
          "human_baseline": 19,
          "completed": true
        },
        {
          "level": 5,
          "score_display": "115.00",
          "actions": 17,
          "human_baseline": 31,
          "completed": true
        },
        {
          "level": 6,
          "score_display": "115.00",
          "actions": 19,
          "human_baseline": 23,
          "completed": true
        },
        {
          "level": 7,
          "score_display": "115.00",
          "actions": 17,
          "human_baseline": 58,
          "completed": true
        },
        {
          "level": 8,
          "score_display": "89.75",
          "actions": 19,
          "human_baseline": 18,
          "completed": true
        }
      ]
    },
    {
      "game_id": "sc25-635fd71a",
      "score_display": "27.11",
      "completed": 3,
      "total_levels": 6,
      "state": "GAME_OVER",
      "actions": 350,
      "resets": 6,
      "replay_url": "https://arcprize.org/replay/ef7a4212-88f8-4008-9478-b62732e37f54",
      "recording_url": "https://arcprize.org/api/recordings/sc25-635fd71a/ef7a4212-88f8-4008-9478-b62732e37f54",
      "levels": [
        {
          "level": 1,
          "score_display": "115.00",
          "actions": 22,
          "human_baseline": 36,
          "completed": true
        },
        {
          "level": 2,
          "score_display": "115.00",
          "actions": 5,
          "human_baseline": 6,
          "completed": true
        },
        {
          "level": 3,
          "score_display": "74.80",
          "actions": 37,
          "human_baseline": 32,
          "completed": true
        },
        {
          "level": 4,
          "score_display": "0.00",
          "actions": 286,
          "human_baseline": 83,
          "completed": false
        },
        {
          "level": 5,
          "score_display": "0.00",
          "actions": 0,
          "human_baseline": 143,
          "completed": false
        },
        {
          "level": 6,
          "score_display": "0.00",
          "actions": 0,
          "human_baseline": 50,
          "completed": false
        }
      ]
    },
    {
      "game_id": "sk48-d8078629",
      "score_display": "15.93",
      "completed": 4,
      "total_levels": 8,
      "state": "GAME_OVER",
      "actions": 1100,
      "resets": 3,
      "replay_url": "https://arcprize.org/replay/87a24a49-c2fe-450c-b627-edc6cff3d26c",
      "recording_url": "https://arcprize.org/api/recordings/sk48-d8078629/87a24a49-c2fe-450c-b627-edc6cff3d26c",
      "levels": [
        {
          "level": 1,
          "score_display": "115.00",
          "actions": 22,
          "human_baseline": 61,
          "completed": true
        },
        {
          "level": 2,
          "score_display": "115.00",
          "actions": 43,
          "human_baseline": 177,
          "completed": true
        },
        {
          "level": 3,
          "score_display": "65.29",
          "actions": 125,
          "human_baseline": 101,
          "completed": true
        },
        {
          "level": 4,
          "score_display": "8.14",
          "actions": 361,
          "human_baseline": 103,
          "completed": true
        },
        {
          "level": 5,
          "score_display": "0.00",
          "actions": 549,
          "human_baseline": 230,
          "completed": false
        },
        {
          "level": 6,
          "score_display": "0.00",
          "actions": 0,
          "human_baseline": 181,
          "completed": false
        },
        {
          "level": 7,
          "score_display": "0.00",
          "actions": 0,
          "human_baseline": 125,
          "completed": false
        },
        {
          "level": 8,
          "score_display": "0.00",
          "actions": 0,
          "human_baseline": 92,
          "completed": false
        }
      ]
    },
    {
      "game_id": "sp80-589a99af",
      "score_display": "47.62",
      "completed": 4,
      "total_levels": 6,
      "state": "GAME_OVER",
      "actions": 550,
      "resets": 11,
      "replay_url": "https://arcprize.org/replay/f4143cf2-f793-494a-8fa8-51137e5d04d2",
      "recording_url": "https://arcprize.org/api/recordings/sp80-589a99af/f4143cf2-f793-494a-8fa8-51137e5d04d2",
      "levels": [
        {
          "level": 1,
          "score_display": "115.00",
          "actions": 6,
          "human_baseline": 39,
          "completed": true
        },
        {
          "level": 2,
          "score_display": "115.00",
          "actions": 8,
          "human_baseline": 58,
          "completed": true
        },
        {
          "level": 3,
          "score_display": "115.00",
          "actions": 10,
          "human_baseline": 25,
          "completed": true
        },
        {
          "level": 4,
          "score_display": "115.00",
          "actions": 45,
          "human_baseline": 148,
          "completed": true
        },
        {
          "level": 5,
          "score_display": "0.00",
          "actions": 481,
          "human_baseline": 96,
          "completed": false
        },
        {
          "level": 6,
          "score_display": "0.00",
          "actions": 0,
          "human_baseline": 152,
          "completed": false
        }
      ]
    },
    {
      "game_id": "su15-1944f8ab",
      "score_display": "45.89",
      "completed": 7,
      "total_levels": 9,
      "state": "GAME_OVER",
      "actions": 400,
      "resets": 7,
      "replay_url": "https://arcprize.org/replay/120c6ea9-eff4-43a7-84f1-3226e9d125f0",
      "recording_url": "https://arcprize.org/api/recordings/su15-1944f8ab/120c6ea9-eff4-43a7-84f1-3226e9d125f0",
      "levels": [
        {
          "level": 1,
          "score_display": "115.00",
          "actions": 9,
          "human_baseline": 22,
          "completed": true
        },
        {
          "level": 2,
          "score_display": "115.00",
          "actions": 21,
          "human_baseline": 42,
          "completed": true
        },
        {
          "level": 3,
          "score_display": "6.90",
          "actions": 99,
          "human_baseline": 26,
          "completed": true
        },
        {
          "level": 4,
          "score_display": "115.00",
          "actions": 14,
          "human_baseline": 115,
          "completed": true
        },
        {
          "level": 5,
          "score_display": "20.25",
          "actions": 80,
          "human_baseline": 36,
          "completed": true
        },
        {
          "level": 6,
          "score_display": "115.00",
          "actions": 12,
          "human_baseline": 31,
          "completed": true
        },
        {
          "level": 7,
          "score_display": "64.00",
          "actions": 10,
          "human_baseline": 8,
          "completed": true
        },
        {
          "level": 8,
          "score_display": "0.00",
          "actions": 155,
          "human_baseline": 40,
          "completed": false
        },
        {
          "level": 9,
          "score_display": "0.00",
          "actions": 0,
          "human_baseline": 41,
          "completed": false
        }
      ]
    },
    {
      "game_id": "tn36-ef4dde99",
      "score_display": "19.11",
      "completed": 4,
      "total_levels": 7,
      "state": "GAME_OVER",
      "actions": 350,
      "resets": 2,
      "replay_url": "https://arcprize.org/replay/de76d875-8b6a-4698-9aba-ba38c805a94b",
      "recording_url": "https://arcprize.org/api/recordings/tn36-ef4dde99/de76d875-8b6a-4698-9aba-ba38c805a94b",
      "levels": [
        {
          "level": 1,
          "score_display": "6.88",
          "actions": 122,
          "human_baseline": 32,
          "completed": true
        },
        {
          "level": 2,
          "score_display": "115.00",
          "actions": 44,
          "human_baseline": 72,
          "completed": true
        },
        {
          "level": 3,
          "score_display": "80.38",
          "actions": 29,
          "human_baseline": 26,
          "completed": true
        },
        {
          "level": 4,
          "score_display": "14.24",
          "actions": 106,
          "human_baseline": 40,
          "completed": true
        },
        {
          "level": 5,
          "score_display": "0.00",
          "actions": 49,
          "human_baseline": 30,
          "completed": false
        },
        {
          "level": 6,
          "score_display": "0.00",
          "actions": 0,
          "human_baseline": 55,
          "completed": false
        },
        {
          "level": 7,
          "score_display": "0.00",
          "actions": 0,
          "human_baseline": 62,
          "completed": false
        }
      ]
    },
    {
      "game_id": "tr87-cd924810",
      "score_display": "27.09",
      "completed": 4,
      "total_levels": 6,
      "state": "GAME_OVER",
      "actions": 450,
      "resets": 1,
      "replay_url": "https://arcprize.org/replay/2b7532a6-d626-4eeb-b3cd-ff8722290f36",
      "recording_url": "https://arcprize.org/api/recordings/tr87-cd924810/2b7532a6-d626-4eeb-b3cd-ff8722290f36",
      "levels": [
        {
          "level": 1,
          "score_display": "78.37",
          "actions": 61,
          "human_baseline": 54,
          "completed": true
        },
        {
          "level": 2,
          "score_display": "6.70",
          "actions": 224,
          "human_baseline": 58,
          "completed": true
        },
        {
          "level": 3,
          "score_display": "59.17",
          "actions": 52,
          "human_baseline": 40,
          "completed": true
        },
        {
          "level": 4,
          "score_display": "74.89",
          "actions": 52,
          "human_baseline": 45,
          "completed": true
        },
        {
          "level": 5,
          "score_display": "0.00",
          "actions": 61,
          "human_baseline": 71,
          "completed": false
        },
        {
          "level": 6,
          "score_display": "0.00",
          "actions": 0,
          "human_baseline": 146,
          "completed": false
        }
      ]
    },
    {
      "game_id": "tu93-0768757b",
      "score_display": "62.20",
      "completed": 8,
      "total_levels": 9,
      "state": "GAME_OVER",
      "actions": 500,
      "resets": 24,
      "replay_url": "https://arcprize.org/replay/92e41630-5e7a-49fc-970f-6cb029d666c8",
      "recording_url": "https://arcprize.org/api/recordings/tu93-0768757b/92e41630-5e7a-49fc-970f-6cb029d666c8",
      "levels": [
        {
          "level": 1,
          "score_display": "111.42",
          "actions": 18,
          "human_baseline": 19,
          "completed": true
        },
        {
          "level": 2,
          "score_display": "113.78",
          "actions": 15,
          "human_baseline": 16,
          "completed": true
        },
        {
          "level": 3,
          "score_display": "115.00",
          "actions": 19,
          "human_baseline": 34,
          "completed": true
        },
        {
          "level": 4,
          "score_display": "115.00",
          "actions": 17,
          "human_baseline": 42,
          "completed": true
        },
        {
          "level": 5,
          "score_display": "115.00",
          "actions": 29,
          "human_baseline": 123,
          "completed": true
        },
        {
          "level": 6,
          "score_display": "8.91",
          "actions": 268,
          "human_baseline": 80,
          "completed": true
        },
        {
          "level": 7,
          "score_display": "100.00",
          "actions": 14,
          "human_baseline": 14,
          "completed": true
        },
        {
          "level": 8,
          "score_display": "40.82",
          "actions": 36,
          "human_baseline": 23,
          "completed": true
        },
        {
          "level": 9,
          "score_display": "0.00",
          "actions": 84,
          "human_baseline": 111,
          "completed": false
        }
      ]
    },
    {
      "game_id": "vc33-5430563c",
      "score_display": "72.27",
      "completed": 7,
      "total_levels": 7,
      "state": "WIN",
      "actions": 446,
      "resets": 2,
      "replay_url": "https://arcprize.org/replay/66c0097f-c27e-4a7a-bcc1-c5607a8e8f22",
      "recording_url": "https://arcprize.org/api/recordings/vc33-5430563c/66c0097f-c27e-4a7a-bcc1-c5607a8e8f22",
      "levels": [
        {
          "level": 1,
          "score_display": "28.99",
          "actions": 13,
          "human_baseline": 7,
          "completed": true
        },
        {
          "level": 2,
          "score_display": "115.00",
          "actions": 8,
          "human_baseline": 18,
          "completed": true
        },
        {
          "level": 3,
          "score_display": "115.00",
          "actions": 24,
          "human_baseline": 44,
          "completed": true
        },
        {
          "level": 4,
          "score_display": "115.00",
          "actions": 28,
          "human_baseline": 61,
          "completed": true
        },
        {
          "level": 5,
          "score_display": "115.00",
          "actions": 47,
          "human_baseline": 131,
          "completed": true
        },
        {
          "level": 6,
          "score_display": "22.30",
          "actions": 72,
          "human_baseline": 34,
          "completed": true
        },
        {
          "level": 7,
          "score_display": "35.81",
          "actions": 254,
          "human_baseline": 152,
          "completed": true
        }
      ]
    },
    {
      "game_id": "wa30-ee6fef47",
      "score_display": "39.81",
      "completed": 6,
      "total_levels": 9,
      "state": "GAME_OVER",
      "actions": 1000,
      "resets": 5,
      "replay_url": "https://arcprize.org/replay/3e15e187-8142-457c-9a35-41448c3ae511",
      "recording_url": "https://arcprize.org/api/recordings/wa30-ee6fef47/3e15e187-8142-457c-9a35-41448c3ae511",
      "levels": [
        {
          "level": 1,
          "score_display": "115.00",
          "actions": 36,
          "human_baseline": 71,
          "completed": true
        },
        {
          "level": 2,
          "score_display": "115.00",
          "actions": 59,
          "human_baseline": 119,
          "completed": true
        },
        {
          "level": 3,
          "score_display": "95.77",
          "actions": 187,
          "human_baseline": 183,
          "completed": true
        },
        {
          "level": 4,
          "score_display": "4.50",
          "actions": 462,
          "human_baseline": 98,
          "completed": true
        },
        {
          "level": 5,
          "score_display": "115.00",
          "actions": 110,
          "human_baseline": 368,
          "completed": true
        },
        {
          "level": 6,
          "score_display": "94.37",
          "actions": 70,
          "human_baseline": 68,
          "completed": true
        },
        {
          "level": 7,
          "score_display": "0.00",
          "actions": 76,
          "human_baseline": 79,
          "completed": false
        },
        {
          "level": 8,
          "score_display": "0.00",
          "actions": 0,
          "human_baseline": 442,
          "completed": false
        },
        {
          "level": 9,
          "score_display": "0.00",
          "actions": 0,
          "human_baseline": 415,
          "completed": false
        }
      ]
    }
  ]
}''')


def reconstruct():
    games = DATA["games"]
    assert len(games) == 25
    assert len({g["game_id"] for g in games}) == 25
    game_scores, caps = [], []
    completed = actions = resets = available = max_efficiency = wins = 0
    for g in games:
        levels = g["levels"]
        n = g["total_levels"]
        assert len(levels) == n
        assert [l["level"] for l in levels] == list(range(1, n + 1))
        assert sum(l["completed"] for l in levels) == g["completed"]
        assert sum(l["actions"] for l in levels) == g["actions"]
        assert 0 <= g["resets"] <= g["actions"]
        W = n * (n + 1) / 2
        weighted_done = weighted_efficiency = 0.0
        for l in levels:
            assert l["actions"] >= 0 and l["human_baseline"] > 0
            q = 0.0
            if l["completed"]:
                assert l["actions"] > 0
                q = min(1.15, (l["human_baseline"] / l["actions"]) ** 2)
                weighted_done += l["level"]
                max_efficiency += int(math.isclose(q, 1.15, abs_tol=1e-12))
            assert f"{100 * q:.2f}" == l["score_display"], (g["game_id"], l["level"])
            weighted_efficiency += l["level"] * q
        cap = 100 * weighted_done / W
        score = min(cap, 100 * weighted_efficiency / W)
        assert f"{score:.2f}" == g["score_display"], g["game_id"]
        assert (g["state"] == "WIN") == (g["completed"] == n)
        game_scores.append(score)
        caps.append(cap)
        completed += g["completed"]
        available += n
        actions += g["actions"]
        resets += g["resets"]
        wins += int(g["state"] == "WIN")
    rhae = math.fsum(game_scores) / len(games)
    cap_mean = math.fsum(caps) / len(games)
    assert (completed, available, wins, actions, resets, max_efficiency) == (124, 183, 7, 15710, 122, 82)
    assert math.isclose(rhae, 46.13299057187088, abs_tol=1e-10)
    assert math.isclose(cap_mean, 53.66378066378068, abs_tol=1e-10)
    return {
        "source_url": DATA["source_url"],
        "games": len(games), "levels_completed": completed,
        "levels_available": available, "games_won": wins,
        "actions_including_resets": actions, "resets": resets,
        "rhae_percent": rhae,
        "pooled_completion_percent": 100 * completed / available,
        "weighted_completion_cap_percent": cap_mean,
        "net_efficiency_loss_percentage_points": cap_mean - rhae,
        "completed_levels_at_1_15": max_efficiency,
        "historical_baseline_difference_percentage_points": rhae - 23.16434010,
        "recorded_action_ratio_to_historical_baseline": actions / 2475,
        "interpretation": "Descriptive scorecard comparison; no execution-lineage, causal, or cost validation",
    }




# Final local extension from the committed report; it is not part of DATA's
# official replay checkpoint. The report is pinned so later edits do not change
# the meaning of these counts.
FINAL_SOURCE = "https://github.com/dcw06/ARC-AGI-3/tree/756d8851e0826d74803e314306a6609f06fc0530/reports/baseline_continue_v1"
CAPS = {"ar25":750,"bp35":700,"cd82":200,"cn04":800,"dc22":1250,"ft09":100,"g50t":900,"ka59":750,"lf52":1350,"lp85":400,"ls20":800,"m0r0":1150,"r11l":250,"re86":1300,"s5i5":650,"sb26":150,"sc25":350,"sk48":1100,"sp80":550,"su15":400,"tn36":350,"tr87":450,"tu93":500,"vc33":450,"wa30":1850}
FINAL_WA30_ACTIONS = [36, 59, 187, 462, 110, 70, 244, 682, 0]


def latest_round2():
    import copy
    published = reconstruct()
    games = copy.deepcopy(DATA["games"])
    wa = next(g for g in games if g["game_id"].startswith("wa30-"))
    assert (wa["actions"], wa["completed"], wa["resets"]) == (1000, 6, 5)
    assert sum(FINAL_WA30_ACTIONS) == 1850
    # Reported batch calls: 299 in 300 actions; 546 in 550 actions.
    extra_resets = (300 - 299) + (550 - 546)
    assert extra_resets == 5
    wa["actions"], wa["completed"] = 1850, 7
    wa["resets"] += extra_resets
    for l, count in zip(wa["levels"], FINAL_WA30_ACTIONS):
        l["actions"] = count
        l["completed"] = l["level"] <= wa["completed"]
    scores, caps, max_efficiency = [], [], 0
    for g in games:
        assert sum(l["actions"] for l in g["levels"]) == g["actions"]
        assert sum(l["completed"] for l in g["levels"]) == g["completed"]
        assert g["actions"] <= CAPS[g["game_id"].split("-")[0]]
        n = g["total_levels"]
        W = n * (n + 1) / 2
        cap = 100 * g["completed"] * (g["completed"] + 1) / 2 / W
        efficiency = 0.0
        for l in g["levels"]:
            if l["completed"]:
                assert l["actions"] > 0
                q = min(1.15, (l["human_baseline"] / l["actions"]) ** 2)
                efficiency += l["level"] * q
                max_efficiency += int(math.isclose(q, 1.15, abs_tol=1e-12))
        score = min(cap, 100 * efficiency / W)
        scores.append(score)
        caps.append(cap)
        if g is wa:
            wa_score = score
    actions = sum(g["actions"] for g in games)
    resets = sum(g["resets"] for g in games)
    completed = sum(g["completed"] for g in games)
    available = sum(g["total_levels"] for g in games)
    wins = sum(g["completed"] == g["total_levels"] for g in games)
    rhae = math.fsum(scores) / len(games)
    cap_mean = math.fsum(caps) / len(games)
    assert sum(CAPS.values()) == 17500
    assert (actions, resets, completed, available, wins, max_efficiency) == (16560, 127, 125, 183, 7, 82)
    assert math.isclose(rhae, 46.19821646694089, abs_tol=1e-10)
    assert math.isclose(wa_score, 41.44187593054268, abs_tol=1e-10)
    assert math.isclose(cap_mean, 54.286002886002876, abs_tol=1e-10)
    return {
        "source_url": FINAL_SOURCE,
        "evidence_status": "Completed local round; expected score, not a new official scorecard",
        "games": len(games), "levels_completed": completed,
        "levels_available": available, "games_won": wins,
        "actions_including_resets": actions, "resets": resets,
        "total_game_caps": sum(CAPS.values()),
        "expected_rhae_percent": rhae,
        "pooled_completion_percent": 100 * completed / available,
        "weighted_completion_cap_percent": cap_mean,
        "net_efficiency_loss_percentage_points": cap_mean - rhae,
        "completed_levels_at_1_15": max_efficiency,
        "wa30_actions": wa["actions"], "wa30_resets": wa["resets"],
        "wa30_levels_completed": wa["completed"],
        "wa30_expected_game_score_percent": wa_score,
        "actions_added_after_official_checkpoint": actions - published["actions_including_resets"],
        "resets_added_after_official_checkpoint": extra_resets,
        "historical_baseline_difference_percentage_points": rhae - 23.16434009999122,
        "recorded_action_ratio_to_historical_baseline": actions / 2475,
    }


if __name__ == "__main__":
    print("HISTORICAL CHECKER: November 20 checkpoint and offline extension. Later official confirmation is checked by verify_layered.py.")
    print(json.dumps({"official_replay_checkpoint": reconstruct(),
                      "completed_second_round": latest_round2()}, indent=2))
