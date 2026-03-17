// useI18n — hook React para internacionalização
import { useState, useEffect, useCallback } from "react";
import { t, getLocale, setLocale, type Locale } from "../i18n";

/**
 * Hook que fornece função de tradução `t()` e troca de idioma reativa.
 *
 * Uso:
 *   const { t, locale, changeLocale } = useI18n();
 *   <button>{t("common.save")}</button>
 *   <button onClick={() => changeLocale("en")}>EN</button>
 */
export function useI18n() {
  const [locale, setLocaleState] = useState<Locale>(getLocale);

  useEffect(() => {
    const handler = (e: Event) => {
      setLocaleState((e as CustomEvent<Locale>).detail);
    };
    window.addEventListener("wifisense:locale-changed", handler);
    return () => window.removeEventListener("wifisense:locale-changed", handler);
  }, []);

  const changeLocale = useCallback((l: Locale) => {
    setLocale(l);
  }, []);

  return { t, locale, changeLocale };
}
