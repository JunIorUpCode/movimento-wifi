// i18n — sistema de internacionalização WiFiSense (PT-BR / EN)
import { ptBR } from "./pt-BR";
import { en } from "./en";

export type Locale = "pt-BR" | "en";

const STORAGE_KEY = "wifisense_locale";

const translations: Record<Locale, typeof ptBR> = { "pt-BR": ptBR, en };

function detectLocale(): Locale {
  const stored = localStorage.getItem(STORAGE_KEY) as Locale | null;
  if (stored && stored in translations) return stored;
  const browser = navigator.language.startsWith("pt") ? "pt-BR" : "en";
  return browser;
}

let _current: Locale = detectLocale();
let _t = translations[_current];

/** Retorna a string traduzida usando dot-notation. Ex: t("common.save") */
export function t(key: string): string {
  const parts = key.split(".");
  // eslint-disable-next-line @typescript-eslint/no-explicit-any
  let value: any = _t;
  for (const part of parts) {
    value = value?.[part];
  }
  return typeof value === "string" ? value : key;
}

/** Retorna o locale atual. */
export function getLocale(): Locale {
  return _current;
}

/** Muda o locale e persiste no localStorage. Requer re-render dos componentes. */
export function setLocale(locale: Locale): void {
  _current = locale;
  _t = translations[locale];
  localStorage.setItem(STORAGE_KEY, locale);
  // Dispara evento customizado para que componentes possam reagir
  window.dispatchEvent(new CustomEvent("wifisense:locale-changed", { detail: locale }));
}

export { ptBR, en };
