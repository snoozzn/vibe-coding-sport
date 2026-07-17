# ============================================================
# VibeSport Backend - Services 包
# ============================================================
from services.auth_service import (
    register_user,
    login_user,
    get_user_profile,
    update_user_profile,
    change_password,
)
from services.running_service import (
    create_running_log,
    get_running_logs,
    get_running_log,
    update_running_log,
    delete_running_log,
    get_running_stats,
)
from services.fitness_service import (
    create_fitness_log,
    get_fitness_logs,
    get_fitness_log,
    update_fitness_log,
    delete_fitness_log,
    get_fitness_stats,
)
from services.weight_service import (
    create_weight_log,
    get_weight_logs,
    get_weight_log,
    update_weight_log,
    delete_weight_log,
    get_weight_stats,
    get_weight_trend,
)
from services.exercise_service import (
    get_all_exercise_types,
    get_preset_exercise_types,
    create_custom_type,
)
from services.dashboard_service import get_dashboard

__all__ = [
    # auth
    "register_user",
    "login_user",
    "get_user_profile",
    "update_user_profile",
    "change_password",
    # running
    "create_running_log",
    "get_running_logs",
    "get_running_log",
    "update_running_log",
    "delete_running_log",
    "get_running_stats",
    # fitness
    "create_fitness_log",
    "get_fitness_logs",
    "get_fitness_log",
    "update_fitness_log",
    "delete_fitness_log",
    "get_fitness_stats",
    # weight
    "create_weight_log",
    "get_weight_logs",
    "get_weight_log",
    "update_weight_log",
    "delete_weight_log",
    "get_weight_stats",
    "get_weight_trend",
    # exercise
    "get_all_exercise_types",
    "get_preset_exercise_types",
    "create_custom_type",
    # dashboard
    "get_dashboard",
]
