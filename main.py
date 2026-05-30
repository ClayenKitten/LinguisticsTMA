import streamlit as st
import pandas as pd
import plotly.express as px

from data import Dataset, PartOfSpeech, Word, episodes_to_dataframe


def main():
    dataset = Dataset.load()

    print_header()
    st.divider()
    print_episode_analysis(dataset)
    st.divider()
    print_comparison_analysis(dataset)


def print_header():
    _, col, _ = st.columns(3)
    with col:
        st.image("media/tma.webp")

    title = "Репрезентация концепта FEAR в аудиодраме The Magnus Archives"
    st.title(title, text_alignment="center", anchor=False)
    st.set_page_config(page_icon="media/tma.webp")
    st.set_page_config(page_title=title)


def print_episode_analysis(dataset: Dataset):
    st.header("Анализ средств репрезентации", anchor=False)
    st.write(f"В работе было рассмотрено {len(dataset.episodes)} эпизодов аудиодрамы.")

    episode_tabs = st.tabs([e.title for e in dataset.episodes])
    for i, episode_tab in enumerate(episode_tabs):
        episode = dataset.episodes[i]
        with episode_tab:
            with st.container(border=True):
                # Транскрипт
                with st.expander(label="Транскрипт эпизода"):
                    st.text(episode.transcript)
                # Слова
                st.subheader(f"Слова", anchor=False)
                st.text(
                    "При рассмотрении данного эпизода можно отметить следующие средства реализации концепта FEAR:"
                )
                titles: dict[str, PartOfSpeech | None] = {
                    f"Все ({(episode.word_count())})": None,
                    f"Существительные и местоимения ({episode.word_count("noun")})": "noun",
                    f"Прилагательные ({episode.word_count("adjective")})": "adjective",
                    f"Глаголы ({episode.word_count("verb")})": "verb",
                    f"Наречия ({episode.word_count("adverb")})": "adverb",
                }
                wordcategory_tabs = st.tabs(list(titles.keys()))
                for j, wordcategory_tab in enumerate(wordcategory_tabs):
                    category = list(titles.values())[j]
                    with wordcategory_tab:
                        st.write(
                            ", ".join(
                                [
                                    f"{e.word} ({e.count})"
                                    for e in episode.words_by_category(category)
                                ]
                            )
                        )
                st.subheader(f"Ядерные лексемы", anchor=False)
                st.text(f"Ядро: {", ".join(episode.lexems.kernel_words)}.")
                st.text(f"Ближняя периферия: {", ".join(episode.lexems.close_words)}.")
                st.text(f"Дальняя периферия: {", ".join(episode.lexems.far_words)}.")
                st.markdown(
                    episode.lexems.build_svg(), width="stretch", unsafe_allow_html=True
                )


def print_comparison_analysis(dataset: Dataset):
    st.header("Сравнительно-сопоставительный анализ", anchor=False)

    col1, col2 = st.columns([2, 1])
    with col1:
        selected_episodes = st.multiselect(
            "Эпизоды", dataset.episodes, default=dataset.episodes
        )
    with col2:
        selected_part_of_speech: PartOfSpeech | None = st.selectbox(
            "Часть речи",
            [None, *Word.all_parts_of_speech()],
            format_func=lambda v: {
                None: "Все",
                "noun": "Существительные",
                "adjective": "Прилагательные",
                "verb": "Глагол",
                "adverb": "Наречие",
            }[v],
        )
        pass

    if len(selected_episodes) < 2:
        st.warning("Выберите хотя бы два эпизода.", icon="⚠️")
        return

    only_with_multiple = st.checkbox(
        "Показывать только слова, встречающиеся более чем в одном эпизоде.", True
    )

    heatmap, barchart, table = st.tabs(
        ["Тепловая карта", "Столбчатая диаграмма", "Таблица"]
    )

    df = episodes_to_dataframe(
        selected_episodes, selected_part_of_speech, only_with_multiple
    )

    with heatmap:
        fig = px.imshow(
            df, text_auto=True, aspect="auto", color_continuous_scale="ylgn"
        )
        fig.update_xaxes(side="top", title=None)
        fig.update_yaxes(title=None)
        fig.update_layout(
            dragmode=False,
            coloraxis_showscale=False,
            xaxis=dict(fixedrange=True),
            yaxis=dict(fixedrange=True),
        )
        fig.update_layout(height=max(400, len(df) * 28))
        st.plotly_chart(fig, width="stretch")
    with barchart:
        fig = px.bar(df[::-1], orientation="h")
        fig.update_xaxes(side="top", title=None)
        fig.update_yaxes(title=None)
        fig.update_layout(
            dragmode=False,
            coloraxis_showscale=False,
            xaxis=dict(fixedrange=True),
            yaxis=dict(fixedrange=True),
        )
        fig.update_layout(height=max(400, len(df) * 28))
        st.plotly_chart(fig, width="stretch")
    with table:
        st.dataframe(df, placeholder="")


if __name__ == "__main__":
    main()
