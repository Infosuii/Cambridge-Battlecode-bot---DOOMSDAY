# EXP-097 field-order cost breakdown

Both draft and all 11 native round-one suspensions matched the originals. Cache setup cost roughly 1,212–1,236 fuel. The packed key loop used 9,870 on the first map and 11,194 on the second. Sorting cost about 6,474 and 6,621, and writing the result to the second vector cost 2,468 and 2,676. Pool_604376 crossed during sorting, and pool_604288 crossed while writing the second vector. [Measured parts](FIELD_ORDER_PARTS.json).
