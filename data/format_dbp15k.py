from .kg_path import kg_data_dir
from pathlib import Path

'''
root\
   entity2id_en.txt
   entity2id_zh.txt
   relation2id_en.txt
   relation2id_zh.txt
   triples_zh.txt
   triples_en.txt
   entity_seeds.txt
   relation_seeds.txt
   JAPE\
      0_3\
         train_entity_seeds.txt
         train_relation_seeds.txt
         test_entity_seeds.txt
        #  test_relation_seeds.txt JAPE中relation seed没有测试集
   OpenKE\
      en\
         entity2id.txt
         relation2id.txt
         train2id.txt
         valid2id.txt
         type_constrain.txt
      zh\
'''

def _dump_seeds(file, file_name, bin_dir):
    with open(bin_dir / (file_name + '_seeds.txt'), 'w', encoding='utf8') as f:
        f.write(str(len(file)) + '\n')
        for seed_pair in file:
            f.write('\t'.join(str(i) for i in seed_pair) + '\n')

def format_dbp15k(bin_dir):
    bin_dir = Path(bin_dir)
    if not bin_dir.exists():
        bin_dir.mkdir()
    bin_dir = bin_dir / 'dbp15k'
    if bin_dir.exists:
        import shutil
        shutil.rmtree(bin_dir)
        bin_dir.mkdir()

    def _format_seeds(mapping_sr, mapping_tg, bin_dir, directory, language):

        file2path = {'entity': 'ent_ILLS', 'relation': 'rel_ILLS'}
        type2seeds = {}
        for seed_type, path in file2path.items():
            file2id_sr = mapping_sr[seed_type]
            file2id_tg = mapping_tg[seed_type]
            with open(directory / path, 'r', encoding='utf8') as f:
                lines = f.readlines()
            seed_pairs = [line.strip().split('\t') for line in lines]
            seed_pairs = [(file2id_sr[seed_pair[0]], file2id_tg[seed_pair[1]])
                          for seed_pair in seed_pairs]
            _dump_seeds(seed_pairs, seed_type, bin_dir)
            type2seeds[seed_type] = seed_pairs
        return type2seeds

    def _format_single_language(directory, bin_dir, language):
        def _dump_mapping(file, file_name, bin_dir, language):
            with open(bin_dir / (file_name + '_' + language + '.txt'), 'w', encoding='utf8') as f:
                # print(file[:10])

                sorted_file = sorted(file.items(), key=lambda x: x[1])
                f.write(str(len(sorted_file)) + '\n')
                for item, i in sorted_file:
                    f.write(item + '\t' + str(i) + '\n')

        def _dump_triples(file, file_name, bin_dir, language):
            with open(bin_dir / (file_name + '_' + language + '.txt'), 'w', encoding='utf8') as f:
                f.write(str(len(file)) + '\n')
                for head, relation, tail in file:
                    f.write(str(head) + '\t' + str(tail) +
                            '\t' + str(relation) + '\n')

        entities = set()
        relations = set()
        if language == 'en':
            triples_path = 't_triples'
        else:
            triples_path = 's_triples'
        with open(directory / triples_path, 'r', encoding='utf8') as f:
            lines = f.readlines()
            lines = [line.strip().split('\t') for line in lines]
            for line in lines:
                entities.add(line[0])
                entities.add(line[2])
                relations.add(line[1])
        entity2id = {entity: i for i, entity in enumerate(entities)}
        relation2id = {relation: i for i,
                       relation in enumerate(relations)}
        triples = [(entity2id[line[0]], relation2id[line[1]],
                    entity2id[line[2]]) for line in lines]

        _dump_mapping(entity2id, 'entity2id', bin_dir, language)
        _dump_mapping(relation2id, 'relation2id', bin_dir, language)
        _dump_triples(triples, 'triples', bin_dir, language)
        return {'entity': entity2id, 'relation': relation2id}, triples

    def _format_overall(directory, bin_dir, language_sr, language_tg='en'):
        '''
        sr: source
        tg: target
        '''
        if not bin_dir.exists():
            bin_dir.mkdir()
        mapping_sr, triples_sr = _format_single_language(
            directory, bin_dir, language_sr)
        mapping_tg, triples_tg = _format_single_language(
            directory, bin_dir, language_tg)
        type2seeds = _format_seeds(
            mapping_sr, mapping_tg, bin_dir, directory, language)

        return (mapping_sr, mapping_tg, triples_sr, triples_tg, type2seeds)

    _local_data_dir = kg_data_dir / 'dbp15k'
    language_pair_paths = list(_local_data_dir.glob('*_en'))
    language2dir = {path.name.split(
        '_')[0]: path for path in language_pair_paths}

    for language, directory in language2dir.items():
        local_bin_dir = bin_dir / (language + '_' + 'en')
        mapping_sr, mapping_tg, triples_sr, triples_tg, type2seeds = _format_overall(directory, local_bin_dir, language, 'en')
        _format_JAPE(directory, local_bin_dir, mapping_sr, mapping_tg)


def _format_JAPE(directory, bin_dir, mapping_sr, mapping_tg):
    def _read_mapping(path):
        with open(path, 'r', encoding='utf8') as f:
            lines = f.readlines()
            lines = [line.strip().split('\t') for line in lines]
            return dict(lines)

    def _get_local_mapping(directory):
        id2relation_sr = _read_mapping(directory / 'rel_ids_1')
        id2relation_tg = _read_mapping(directory / 'rel_ids_2')
        id2entity_sr = _read_mapping(directory / 'ent_ids_1')
        id2entity_tg = _read_mapping(directory / 'ent_ids_2')
        return {'entity': id2entity_sr, 'relation': id2relation_sr}, {'entity': id2entity_tg, 'relation': id2relation_tg}

    def _read_seeds(path, mapping_sr, mapping_tg):
        with open(path, 'r', encoding='utf8') as f:
            lines = f.readlines()
            lines = [line.strip().split('\t') for line in lines]
            return [(mapping_sr[line[0]], mapping_tg[line[1]])
                    for line in lines]

    def _get_seeds(mapping_sr, mapping_tg, directory):
        train_entity_seeds = _read_seeds(
            directory / 'sup_ent_ids', mapping_sr['entity'], mapping_tg['entity'])
        test_entity_seeds = _read_seeds(
            directory / 'ref_ent_ids', mapping_sr['entity'], mapping_tg['entity'])
        train_relation_seeds = _read_seeds(
            directory / 'sup_rel_ids', mapping_sr['relation'], mapping_tg['relation'])
        return train_entity_seeds, test_entity_seeds, train_relation_seeds

    def _transform2id(seed_pairs, mapping_sr, mapping_tg):
        return [(mapping_sr[seed_pair[0]], mapping_tg[seed_pair[1]]) for seed_pair in seed_pairs]

    bin_dir = bin_dir / 'JAPE'
    if not bin_dir.exists():
        bin_dir.mkdir()

    percent2dir = list(directory.glob('0_*'))
    for directory in percent2dir:
        local_bin_dir = bin_dir / directory.name
        if not local_bin_dir.exists():
            local_bin_dir.mkdir()
        local_mapping_sr, local_mapping_tg = _get_local_mapping(directory)
        train_entity_seeds, test_entity_seeds, train_relation_seeds = _get_seeds(
            local_mapping_sr, local_mapping_tg, directory)
        train_entity_seeds = _transform2id(train_entity_seeds, mapping_sr['entity'], mapping_tg['entity'])
        test_entity_seeds = _transform2id(test_entity_seeds, mapping_sr['entity'], mapping_tg['entity'])
        train_relation_seeds = _transform2id(train_relation_seeds, mapping_sr['relation'], mapping_tg['relation'])
        _dump_seeds(train_entity_seeds, 'train_entity', local_bin_dir)
        _dump_seeds(test_entity_seeds, 'test_entity', local_bin_dir)
        _dump_seeds(train_relation_seeds, 'train_relation', local_bin_dir)

def main(bin_dir):
    format_dbp15k(bin_dir)