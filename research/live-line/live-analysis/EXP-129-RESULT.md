# EXP-129 typed cast rejection

The diagnostic reproduced the original R353 input, scan boundaries, cast attempt and Heart's native suspension. Its added catch work moved the basic attack out of R353, so it failed the original action-prefix condition. On that diagnostic path the official SDK reported error 32, an illegal spell destination, at (39,30). The code alone does not identify the specific destination constraint. [Typed diagnostic](CPG_HEART_CAMP_MASK_REJECTION.json).
