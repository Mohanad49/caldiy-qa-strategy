Feature: Guest booking lifecycle

  Scenario: Booking journey
    Given an isolated Cal.diy event is available
    When a guest books the event
    Then the booking confirmation is shown
    And a correlated confirmation email is delivered

  Scenario: Rescheduling journey
    Given a confirmed guest booking exists
    When the guest reschedules the booking
    Then the replacement booking confirmation is shown
    And a correlated rescheduling email is delivered

  Scenario: Cancellation journey
    Given a confirmed guest booking exists
    When the guest cancels the booking
    Then the cancellation confirmation is shown
    And a correlated cancellation email is delivered
