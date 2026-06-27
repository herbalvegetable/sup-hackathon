# Age-band modifier lookup tables based on LIA Protection Gap Study 2022

AGE_BANDS = [(18, 35), (36, 50), (51, 65), (66, 100)]

CI_AGE_MODIFIER: dict[tuple, float] = {
    (18, 35): 1.0,
    (36, 50): 1.0,
    (51, 65): 0.85,
    (66, 100): 0.70,
}

LIFE_AGE_MODIFIER: dict[tuple, float] = {
    (18, 35): 1.0,
    (36, 50): 1.0,
    (51, 65): 0.75,
    (66, 100): 0.50,
}


def get_modifier(age: int, modifier_table: dict) -> float:
    for (lo, hi), modifier in modifier_table.items():
        if lo <= age <= hi:
            return modifier
    return 1.0


def get_ci_modifier(age: int) -> float:
    return get_modifier(age, CI_AGE_MODIFIER)


def get_life_modifier(age: int) -> float:
    return get_modifier(age, LIFE_AGE_MODIFIER)
