#pragma once
#include "team_tables.h"

void play_draft();
const proxy::Team& imitated_team(); // the team_tables.h row of MIMIC_TEAM (by name), else the pooled "top" row
