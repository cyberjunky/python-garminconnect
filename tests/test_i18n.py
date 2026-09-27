"""Tests for demo interface language selection and localization."""

import builtins
import json
import sys
from pathlib import Path
from types import SimpleNamespace
from typing import Any, cast

import pytest

from garminconnect import i18n

sys.modules.setdefault("readchar", SimpleNamespace(readkey=lambda: "q"))  # type: ignore[arg-type]

import demo  # noqa: E402


@pytest.fixture(autouse=True)
def reset_language() -> None:
    i18n.set_language("en")


def test_english_is_the_deterministic_default() -> None:
    assert i18n.resolve_language() == "en"
    assert i18n.translate("menu.user_profile") == "👤 User & Profile"


def test_explicit_english_selection() -> None:
    assert i18n.resolve_language("en") == "en"
    assert i18n.translate("menu.user_profile", "en") == "👤 User & Profile"


def test_portuguese_translation() -> None:
    assert i18n.translate("menu.user_profile", "pt-BR") == "👤 Usuário e Perfil"


def test_environment_language(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("GARMIN_LANG", "pt-BR")
    assert i18n.resolve_language(env="pt-BR") == "pt-BR"
    assert demo._parse_args([]) is not None
    assert i18n.get_language() == "pt-BR"


def test_cli_language_has_precedence_over_environment(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setenv("GARMIN_LANG", "pt-BR")
    assert i18n.resolve_language("en", "pt-BR") == "en"

    assert demo._parse_args(["--lang", "en"]) is not None
    assert i18n.get_language() == "en"


def test_short_cli_language_option() -> None:
    assert demo._parse_args(["-l", "pt-BR"]) is not None
    assert i18n.get_language() == "pt-BR"


@pytest.mark.parametrize("saved_language", ["en", "pt-BR"])
def test_persisted_language_is_used_when_no_override(
    saved_language: str,
    monkeypatch: pytest.MonkeyPatch,
    tmp_path: Path,
) -> None:
    config_path = tmp_path / "demo_config.json"
    config_path.write_text(json.dumps({"language": saved_language}), encoding="utf-8")
    monkeypatch.setattr(demo, "_demo_config_path", lambda: config_path)
    monkeypatch.delenv("GARMIN_LANG", raising=False)

    assert demo._parse_args([]) is not None
    assert i18n.get_language() == saved_language


@pytest.mark.parametrize(
    "config_contents",
    [None, "", "not json", "{}", '{"language": "fr"}', '{"language": 2}'],
)
def test_invalid_or_missing_persisted_language_falls_back_to_english(
    config_contents: str | None,
    monkeypatch: pytest.MonkeyPatch,
    tmp_path: Path,
) -> None:
    config_path = tmp_path / "demo_config.json"
    if config_contents is not None:
        config_path.write_text(config_contents, encoding="utf-8")
    monkeypatch.setattr(demo, "_demo_config_path", lambda: config_path)
    monkeypatch.delenv("GARMIN_LANG", raising=False)

    assert demo._parse_args([]) is not None
    assert i18n.get_language() == "en"


def test_language_precedence_is_cli_then_environment_then_saved(
    monkeypatch: pytest.MonkeyPatch,
    tmp_path: Path,
) -> None:
    config_path = tmp_path / "demo_config.json"
    config_path.write_text('{"language": "pt-BR"}', encoding="utf-8")
    monkeypatch.setattr(demo, "_demo_config_path", lambda: config_path)
    monkeypatch.setenv("GARMIN_LANG", "en")

    assert demo._parse_args([]) is not None
    assert i18n.get_language() == "en"
    assert demo._parse_args(["--lang", "pt-BR"]) is not None
    assert i18n.get_language() == "pt-BR"


@pytest.mark.parametrize("language", ["en", "pt-BR"])
def test_language_preference_can_be_saved_and_reloaded(
    language: str,
    monkeypatch: pytest.MonkeyPatch,
    tmp_path: Path,
) -> None:
    config_path = tmp_path / ".garminconnect" / "demo_config.json"
    monkeypatch.setattr(demo, "_demo_config_path", lambda: config_path)

    assert demo.save_persisted_language(language) is True
    assert json.loads(config_path.read_text(encoding="utf-8")) == {"language": language}
    assert demo.load_persisted_language() == language


def test_cli_and_environment_overrides_do_not_change_saved_preference(
    monkeypatch: pytest.MonkeyPatch,
    tmp_path: Path,
) -> None:
    config_path = tmp_path / "demo_config.json"
    original = {"language": "pt-BR"}
    config_path.write_text(json.dumps(original), encoding="utf-8")
    monkeypatch.setattr(demo, "_demo_config_path", lambda: config_path)

    monkeypatch.setenv("GARMIN_LANG", "en")
    assert demo._parse_args([]) is not None
    assert json.loads(config_path.read_text(encoding="utf-8")) == original

    assert demo._parse_args(["--lang", "en"]) is not None
    assert json.loads(config_path.read_text(encoding="utf-8")) == original


@pytest.mark.parametrize(
    ("initial", "selection", "expected", "changed_message"),
    [
        ("en", "2", "pt-BR", "Idioma alterado para Português do Brasil."),
        ("pt-BR", "1", "en", "Language changed to English."),
    ],
)
def test_language_selection_changes_runtime_menu_and_persists(
    initial: str,
    selection: str,
    expected: str,
    changed_message: str,
    monkeypatch: pytest.MonkeyPatch,
    tmp_path: Path,
    capsys: pytest.CaptureFixture[str],
) -> None:
    config_path = tmp_path / "demo_config.json"
    monkeypatch.setattr(demo, "_demo_config_path", lambda: config_path)
    i18n.set_language(initial)
    monkeypatch.setattr(demo, "safe_readkey", lambda: selection)

    demo.select_language()
    demo.print_main_menu()

    output = capsys.readouterr().out
    assert i18n.get_language() == expected
    assert changed_message in output
    assert json.loads(config_path.read_text(encoding="utf-8")) == {"language": expected}
    if expected == "pt-BR":
        assert "Usuário e Perfil" in output
        assert "[l] 🌐 Idioma" in output
    else:
        assert "User & Profile" in output
        assert "[l] 🌐 Language" in output


def test_language_submenu_back_does_not_change_or_persist(
    monkeypatch: pytest.MonkeyPatch,
    tmp_path: Path,
) -> None:
    config_path = tmp_path / "demo_config.json"
    monkeypatch.setattr(demo, "_demo_config_path", lambda: config_path)
    i18n.set_language("pt-BR")
    monkeypatch.setattr(demo, "safe_readkey", lambda: "q")

    demo.select_language()

    assert i18n.get_language() == "pt-BR"
    assert not config_path.exists()


def test_language_save_failure_keeps_runtime_change(
    monkeypatch: pytest.MonkeyPatch,
    capsys: pytest.CaptureFixture[str],
) -> None:
    i18n.set_language("en")
    monkeypatch.setattr(demo, "safe_readkey", lambda: "2")
    monkeypatch.setattr(demo, "save_persisted_language", lambda language: False)

    demo.select_language()

    assert i18n.get_language() == "pt-BR"
    assert "Não foi possível salvar a preferência de idioma." in capsys.readouterr().out


def test_language_menu_has_one_l_option_and_preserves_categories(
    capsys: pytest.CaptureFixture[str],
) -> None:
    expected_categories = set("1234567890abcd")
    assert set(demo.menu_categories) == expected_categories

    i18n.set_language("en")
    demo.print_main_menu()
    output = capsys.readouterr().out
    assert output.count("[l] 🌐 Language") == 1


@pytest.mark.parametrize("alias", ["pt_BR", "pt-br", "pt_BR.UTF-8"])
def test_portuguese_aliases_are_normalized(alias: str) -> None:
    assert i18n.normalize_language(alias) == "pt-BR"


def test_unsupported_language_is_friendly() -> None:
    with pytest.raises(
        i18n.UnsupportedLanguageError, match="Available languages: en, pt-BR"
    ):
        i18n.normalize_language("fr")


def test_invalid_cli_language_returns_nonzero_and_clear_message(
    capsys: pytest.CaptureFixture[str],
) -> None:
    assert demo.main(["--lang", "fr"]) == 2
    captured = capsys.readouterr()
    assert "Unsupported language: fr" in captured.err
    assert "Available languages: en, pt-BR" in captured.err


def test_missing_translation_falls_back_to_english(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setitem(i18n._TRANSLATIONS["en"], "test.fallback", "English fallback")
    monkeypatch.delitem(i18n._TRANSLATIONS["pt-BR"], "test.fallback", raising=False)
    assert i18n.translate("test.fallback", "pt-BR") == "English fallback"


def test_dynamic_translation_uses_named_interpolation() -> None:
    assert (
        i18n.translate("menu.heart_rate", "pt-BR", date="2026-09-26")
        == "Obter dados de frequência cardíaca de '2026-09-26'"
    )


def test_menu_is_rendered_in_portuguese(capsys: pytest.CaptureFixture[str]) -> None:
    i18n.set_language("pt-BR")
    demo.print_main_menu()
    output = capsys.readouterr().out
    assert "Usuário e Perfil" in output
    assert "Saúde e Atividade Diárias" in output


def test_prompt_is_rendered_in_portuguese(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    i18n.set_language("pt-BR")
    prompts: list[str] = []
    monkeypatch.setattr(
        builtins,
        "input",
        lambda prompt: prompts.append(prompt) or "123456",
    )
    assert demo.get_mfa() == "123456"
    assert prompts == ["Código único de MFA: "]


def test_api_data_json_filenames_and_user_values_are_not_translated(
    monkeypatch: pytest.MonkeyPatch,
    tmp_path: Any,
    capsys: pytest.CaptureFixture[str],
) -> None:
    i18n.set_language("pt-BR")
    monkeypatch.setattr(demo.config, "export_dir", tmp_path)
    garmin_value = "User & Profile"
    filename = "User & Profile.json"
    response = {"label": garmin_value, "filename": filename}

    demo._display_single("User & Profile", response)

    output = capsys.readouterr().out
    assert json.dumps(response, indent=2) in output
    assert garmin_value in output
    assert filename in output
    assert "Usuário e Perfil" not in output


def test_print_input_and_getpass_are_not_overridden() -> None:
    assert not hasattr(demo, "_localized_print")
    assert not hasattr(demo, "_localized_input")
    assert not hasattr(demo, "_localized_getpass")
    assert not hasattr(demo, "input")
    assert demo.getpass.__module__ == "getpass"
    assert not hasattr(i18n, "translate_text")


def test_menu_api_keys_are_not_translated() -> None:
    categories = cast("Any", demo.menu_categories)
    option = categories["3"]["options"]["1"]
    assert option["key"] == "get_training_readiness"
    assert categories["3"]["options"]["7"]["key"] == "get_hrv_data_range"


def _health_report_data() -> dict[str, Any]:
    return {
        "generated_at": "2026-09-26T12:34:56",
        "user_info": {"full_name": "User & Profile"},
        "today_summary": {
            "totalSteps": 1234,
            "totalKilocalories": 567,
            "totalDistanceMeters": 8900,
            "activeKilocalories": 321,
        },
        "health_metrics": {
            "heart_rate": {"restingHeartRate": 60},
            "sleep": {
                "dailySleepDTO": {
                    "sleepTimeSeconds": 25200,
                    "deepSleepSeconds": 7200,
                }
            },
            "steps": {"totalSteps": 1234, "dailyStepGoal": 10000},
            "stress": {"avgStressLevel": 22},
            "body_battery": [{"charged": 45}],
        },
        "weekly_data": [
            {
                "date": "2026-09-26",
                "totalSteps": 1234,
                "totalKilocalories": 567,
                "totalDistanceMeters": 8900,
            }
        ],
        "recent_activities": [
            {
                "activityName": "Health Metrics",
                "activityType": {"typeKey": "running"},
                "startTimeLocal": "2026-09-26T08:00:00",
                "duration": 3600,
                "distance": 10000,
                "calories": 500,
                "avgHR": 140,
            }
        ],
        "device_info": [
            {
                "displayName": "Device & Profile",
                "productDisplayName": "Unknown",
                "softwareVersion": "1.0",
            }
        ],
    }


def test_health_report_uses_english_labels_and_language_attribute(
    monkeypatch: pytest.MonkeyPatch,
    tmp_path: Path,
) -> None:
    i18n.set_language("en")
    monkeypatch.setattr(demo.config, "export_dir", tmp_path)

    report_path = Path(
        demo.DataExporter.create_readable_health_report(_health_report_data())
    )
    report = report_path.read_text(encoding="utf-8")

    assert '<html lang="en">' in report
    assert "Garmin Health Report" in report
    assert "Today's Activity Summary" in report
    assert "Health Metrics" in report
    assert "User &amp; Profile" in report
    assert "Health Metrics (running)</h4>" in report
    assert "<strong>Model:</strong> Unknown" in report


def test_health_report_uses_portuguese_labels_and_preserves_garmin_data(
    monkeypatch: pytest.MonkeyPatch,
    tmp_path: Path,
) -> None:
    i18n.set_language("pt-BR")
    monkeypatch.setattr(demo.config, "export_dir", tmp_path)

    report_path = Path(
        demo.DataExporter.create_readable_health_report(_health_report_data())
    )
    report = report_path.read_text(encoding="utf-8")

    assert '<html lang="pt-BR">' in report
    assert "Relatório de Saúde da Garmin" in report
    assert "Resumo da Atividade de Hoje" in report
    assert "Passos" in report
    assert "Calorias" in report
    assert "Distância" in report
    assert "Métricas de Saúde" in report
    assert "Frequência Cardíaca" in report
    assert "Sono" in report
    assert "Meta de Passos" in report
    assert "Nível de Estresse" in report
    assert "Tendências Semanais (Últimos 7 Dias)" in report
    assert "Atividades Recentes" in report
    assert "Duração:" in report
    assert "FC Média:" in report
    assert "Informações do Dispositivo" in report
    assert "Modelo:" in report
    assert "Software:" in report
    assert "Gerado pelo Demo da API do Garmin Connect" in report
    assert "Consulte profissionais de saúde" in report

    # These values came from Garmin and must not be looked up in the catalog.
    assert "User &amp; Profile" in report
    assert "Health Metrics (running)</h4>" in report
    assert "<strong>Modelo:</strong> Unknown" in report
    assert "Métricas de Saúde</h2>" in report
    assert "N/D" in report


def test_health_report_translates_empty_state_labels_and_fallbacks(
    monkeypatch: pytest.MonkeyPatch,
    tmp_path: Path,
) -> None:
    i18n.set_language("pt-BR")
    monkeypatch.setattr(demo.config, "export_dir", tmp_path)

    report_path = Path(
        demo.DataExporter.create_readable_health_report(
            {
                "recent_activities": [{}],
                "device_info": [{}],
            }
        )
    )
    report = report_path.read_text(encoding="utf-8")

    assert "Usuário Desconhecido" in report
    assert "Nenhum dado de atividade disponível para hoje" in report
    assert "Nenhum dado de métricas de saúde disponível" in report
    assert "Atividade Desconhecida" in report
    assert "Dispositivo Desconhecido" in report
    assert "Modelo Desconhecido" in report

    empty_report_dir = tmp_path / "empty"
    empty_report_dir.mkdir()
    monkeypatch.setattr(demo.config, "export_dir", empty_report_dir)
    empty_report_path = Path(demo.DataExporter.create_readable_health_report({}))
    empty_report = empty_report_path.read_text(encoding="utf-8")
    assert "Nenhuma atividade recente encontrada" in empty_report


@pytest.mark.parametrize(
    ("language", "fixed_message"),
    [("en", "Unexpected error"), ("pt-BR", "Erro inesperado")],
)
def test_safe_api_call_localizes_fixed_error_and_preserves_exception(
    language: str,
    fixed_message: str,
    capsys: pytest.CaptureFixture[str],
) -> None:
    i18n.set_language(language)
    exception_message = "User & Profile"

    def failing_api_call() -> None:
        raise RuntimeError(exception_message)

    success, result, error_message = demo.safe_api_call(
        failing_api_call, method_name="get_user_profile"
    )

    assert success is False
    assert result is None
    assert error_message is not None
    assert fixed_message in error_message
    assert exception_message in error_message
    output = capsys.readouterr().out
    assert fixed_message in output
    assert exception_message in output


def test_safe_api_call_translates_fixed_not_found_message(
    capsys: pytest.CaptureFixture[str],
) -> None:
    i18n.set_language("pt-BR")

    def missing_api_call() -> None:
        raise demo.GarminConnectNotFoundError("User & Profile")

    demo.safe_api_call(missing_api_call, method_name="get_user_profile")

    output = capsys.readouterr().out
    assert "Endpoint não encontrado" in output
    assert "Endpoint not found" not in output


@pytest.mark.parametrize(
    ("language", "expected"),
    [
        ("en", "Executing: get_full_name"),
        ("pt-BR", "Executando: get_full_name"),
    ],
)
def test_translate_accepts_key_as_named_placeholder(
    language: str,
    expected: str,
) -> None:
    assert i18n.translate("ui.executing", language, key="get_full_name").strip() == (
        f"🔄 {expected}"
    )


@pytest.mark.parametrize(
    ("language", "execution_label"),
    [
        ("en", "Executing: get_full_name"),
        ("pt-BR", "Executando: get_full_name"),
    ],
)
def test_execute_menu_option_with_key_placeholder(
    language: str,
    execution_label: str,
    monkeypatch: pytest.MonkeyPatch,
    tmp_path: Path,
    capsys: pytest.CaptureFixture[str],
) -> None:
    i18n.set_language(language)
    monkeypatch.setattr(demo.config, "export_dir", tmp_path)

    class StubApi:
        def get_full_name(self) -> str:
            return "Ada Lovelace"

    assert demo.menu_categories["1"]["options"]["1"]["key"] == "get_full_name"
    demo.execute_api_call(StubApi(), "get_full_name")

    output = capsys.readouterr().out
    assert execution_label in output
    assert "Ada Lovelace" in output
    assert "got multiple values for argument 'key'" not in output
