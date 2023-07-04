from django_enumfield import enum


class RoleTypeEnum(enum.Enum):
    ADMIN = 1
    MANAGER = 2
    USER = 3
    CARETAKER = 4
    VET = 5
    FINANCE = 6

    labels = {
        ADMIN: "Admin",
        MANAGER: "Manager",
        USER: "User",
        CARETAKER: "Caretaker",
        VET: "Vetenarian",
        FINANCE: "Finance",
    }
