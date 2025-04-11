from splat.notifications.teams.model import (
    TeamsPayloadContentBodyElement,
    TeamsPayloadContentBodyElementAction,
)


def _calculate_size(content: list[TeamsPayloadContentBodyElement]) -> int:
    """Calculate the size of the content in bytes."""
    size = 0
    for element in content:
        json_str = element.model_dump_json(exclude_unset=True, by_alias=True)
        size += len(json_str.encode("utf-8"))
    return size


def create_toggleable_text_block(text: str, title_prefix: str, idx: int) -> list[TeamsPayloadContentBodyElement]:
    lines = text.split("\n")
    first_line = lines[0]
    detail_lines = "\n".join(lines[1:]) if len(lines) > 1 else "No additional details"

    text_id = f"details_{idx}"

    return [
        TeamsPayloadContentBodyElement(
            type="ActionSet",
            actions=[
                TeamsPayloadContentBodyElementAction(
                    type="Action.ToggleVisibility",
                    title=f"{title_prefix} {first_line}",
                    targetElements=[{"elementId": text_id}],
                )
            ],
        ),
        TeamsPayloadContentBodyElement(
            type="TextBlock",
            id=text_id,
            isVisible=False,
            text=detail_lines,
            wrap=True,
        ),
    ]


def add_block_item_to_chunks(
    block_item: list[TeamsPayloadContentBodyElement],
    chunks: list[list[TeamsPayloadContentBodyElement]],
    size_limit: int,
) -> list[list[TeamsPayloadContentBodyElement]]:
    current_chunk = chunks[-1]
    current_size = _calculate_size(current_chunk)

    block_size = _calculate_size(block_item)

    if current_size + block_size > size_limit:
        chunks.append(block_item)
    else:
        current_chunk.extend(block_item)
        chunks[-1] = current_chunk

    return chunks
