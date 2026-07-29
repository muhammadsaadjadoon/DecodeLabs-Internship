import { useEffect, useId, useMemo, useRef, useState } from "react";
import { createPortal } from "react-dom";
import Icon from "./Icon";

export default function PremiumSelect({
  value,
  options,
  onChange,
  ariaLabel,
  disabled = false,
  className = "",
}) {
  const triggerRef = useRef(null);
  const menuRef = useRef(null);
  const listboxId = useId();
  const [open, setOpen] = useState(false);
  const [highlighted, setHighlighted] = useState(0);
  const [position, setPosition] = useState({ top: 0, left: 0, width: 240, maxHeight: 320 });

  const selectedIndex = Math.max(0, options.findIndex((option) => option.value === value));
  const selected = options[selectedIndex] || options[0];

  const optionIds = useMemo(
    () => options.map((_, index) => `${listboxId}-option-${index}`),
    [listboxId, options]
  );

  function updatePosition() {
    const trigger = triggerRef.current;
    if (!trigger) return;
    const rect = trigger.getBoundingClientRect();
    const width = Math.min(Math.max(rect.width, 250), window.innerWidth - 24);
    const estimatedHeight = Math.min(options.length * 44 + 14, 328);
    const spaceBelow = window.innerHeight - rect.bottom - 12;
    const spaceAbove = rect.top - 12;
    const opensUpward = spaceBelow < Math.min(220, estimatedHeight) && spaceAbove > spaceBelow;
    const maxHeight = Math.max(150, Math.min(328, opensUpward ? spaceAbove - 8 : spaceBelow - 8));
    const left = Math.max(12, Math.min(rect.left, window.innerWidth - width - 12));
    const top = opensUpward
      ? Math.max(12, rect.top - Math.min(estimatedHeight, maxHeight) - 8)
      : Math.min(window.innerHeight - Math.min(estimatedHeight, maxHeight) - 12, rect.bottom + 8);

    setPosition({ top, left, width, maxHeight });
  }

  function openMenu() {
    if (disabled) return;
    setHighlighted(selectedIndex);
    updatePosition();
    setOpen(true);
  }

  function choose(option) {
    onChange(option.value);
    setOpen(false);
    requestAnimationFrame(() => triggerRef.current?.focus());
  }

  function moveHighlight(direction) {
    setHighlighted((current) => {
      const next = (current + direction + options.length) % options.length;
      requestAnimationFrame(() => {
        document.getElementById(optionIds[next])?.scrollIntoView({ block: "nearest" });
      });
      return next;
    });
  }

  function handleKeyDown(event) {
    if (disabled) return;
    if (!open && ["ArrowDown", "ArrowUp", "Enter", " "].includes(event.key)) {
      event.preventDefault();
      openMenu();
      return;
    }
    if (!open) return;
    if (event.key === "ArrowDown") {
      event.preventDefault();
      moveHighlight(1);
    } else if (event.key === "ArrowUp") {
      event.preventDefault();
      moveHighlight(-1);
    } else if (event.key === "Home") {
      event.preventDefault();
      setHighlighted(0);
    } else if (event.key === "End") {
      event.preventDefault();
      setHighlighted(options.length - 1);
    } else if (event.key === "Enter" || event.key === " ") {
      event.preventDefault();
      choose(options[highlighted]);
    } else if (event.key === "Escape" || event.key === "Tab") {
      setOpen(false);
    }
  }

  useEffect(() => {
    if (!open) return undefined;
    const handlePointer = (event) => {
      if (!triggerRef.current?.contains(event.target) && !menuRef.current?.contains(event.target)) {
        setOpen(false);
      }
    };
    const handleViewport = () => updatePosition();
    document.addEventListener("pointerdown", handlePointer);
    window.addEventListener("resize", handleViewport);
    window.addEventListener("scroll", handleViewport, true);
    return () => {
      document.removeEventListener("pointerdown", handlePointer);
      window.removeEventListener("resize", handleViewport);
      window.removeEventListener("scroll", handleViewport, true);
    };
  }, [open]);

  return (
    <div className={`premium-select ${className} ${open ? "open" : ""}`}>
      <button
        ref={triggerRef}
        type="button"
        className="premium-select-trigger"
        aria-label={ariaLabel}
        aria-haspopup="listbox"
        aria-expanded={open}
        aria-controls={open ? listboxId : undefined}
        disabled={disabled}
        onClick={() => (open ? setOpen(false) : openMenu())}
        onKeyDown={handleKeyDown}
      >
        <span className="premium-select-value">{selected?.label || "Select"}</span>
        <span className="premium-select-chevron"><Icon name="chevronDown" size={17} /></span>
      </button>

      {open && createPortal(
        <div
          ref={menuRef}
          id={listboxId}
          className={`premium-select-menu ${className ? `${className}-menu` : ""}`}
          role="listbox"
          aria-label={ariaLabel}
          aria-activedescendant={optionIds[highlighted]}
          tabIndex={-1}
          onKeyDown={handleKeyDown}
          style={{
            top: `${position.top}px`,
            left: `${position.left}px`,
            width: `${position.width}px`,
            maxHeight: `${position.maxHeight}px`,
          }}
        >
          {options.map((option, index) => {
            const isSelected = option.value === value;
            const isHighlighted = index === highlighted;
            return (
              <button
                type="button"
                id={optionIds[index]}
                key={option.value}
                className={`premium-select-option ${isSelected ? "selected" : ""} ${isHighlighted ? "highlighted" : ""}`}
                role="option"
                aria-selected={isSelected}
                onMouseEnter={() => setHighlighted(index)}
                onClick={() => choose(option)}
              >
                <span>
                  <strong>{option.label}</strong>
                  {option.description && <small>{option.description}</small>}
                </span>
                {isSelected && <Icon name="check" size={16} />}
              </button>
            );
          })}
        </div>,
        document.body
      )}
    </div>
  );
}
