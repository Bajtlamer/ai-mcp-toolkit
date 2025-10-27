<script>
  export let lines = 3;
  export let height = 'h-4';
  export let fullWidth = true;
</script>

<div class="animate-pulse space-y-3">
  {#each Array(lines) as _, i}
    <div 
      class="{height} bg-gray-200 dark:bg-gray-700 rounded {fullWidth ? 'w-full' : i === lines - 1 ? 'w-3/4' : 'w-full'}"
    ></div>
  {/each}
</div>
