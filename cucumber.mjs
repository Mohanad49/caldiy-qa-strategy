export default {
  paths: ["tests/bdd/features/**/*.feature"],
  import: ["tests/bdd/support/**/*.ts", "tests/bdd/steps/**/*.ts"],
  format: [
    "progress-bar",
    "json:test-results/bdd/cucumber.json",
    "junit:test-results/bdd/junit.xml"
  ],
  parallel: 0,
  retry: 0,
  publish: false
};
