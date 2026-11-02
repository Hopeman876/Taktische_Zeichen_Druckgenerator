// Unter Windows kein zusaetzliches Konsolenfenster im Release-Build.
#![cfg_attr(not(debug_assertions), windows_subsystem = "windows")]

fn main() {
    tz_app_lib::run();
}
