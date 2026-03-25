from blackjack.models import Card, Shoe


class HiLoCounter:
    def __init__(self, shoe: Shoe):
        self._shoe = shoe
        self.running_count: int = 0

    def update(self, card: Card) -> None:
        self.running_count += card.hi_lo_value

    @property
    def true_count(self) -> float:
        return self.running_count / self._shoe.decks_remaining

    def reset(self) -> None:
        self.running_count = 0
