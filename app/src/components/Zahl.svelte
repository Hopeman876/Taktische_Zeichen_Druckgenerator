<script lang="ts">
  // Beschriftetes Zahlenfeld.
  let {
    label,
    wert = $bindable(),
    min,
    max,
    schritt = 0.5,
    einheit = "",
    onchange,
  }: {
    label: string;
    wert: number;
    min?: number;
    max?: number;
    schritt?: number;
    einheit?: string;
    onchange?: () => void;
  } = $props();
</script>

<label class="feld">
  <span>{label}{#if einheit}<span class="muted"> ({einheit})</span>{/if}</span>
  <input type="number" bind:value={wert} {min} {max} step={schritt} onchange={() => onchange?.()} />
</label>
