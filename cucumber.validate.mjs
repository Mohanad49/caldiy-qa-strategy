export default {
  paths: ["tests/bdd/features/**/*.feature"],
  import: ["tests/bdd/support/**/*.ts", "tests/bdd/steps/**/*.ts"],
  format: ["progress"],
  parallel: 0,
  retry: 0,
  publish: false
};
