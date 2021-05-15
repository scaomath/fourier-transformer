from libs import *
import argparse
import torch.autograd.profiler as profiler
DEBUG = False


def main():

    # Training settings
    parser = argparse.ArgumentParser(
        description='Memory profiling of various transformers for Example 1')
    parser.add_argument('--batch-size', type=int, default=4, metavar='N',
                        help='input batch size for profiling (default: 4)')
    parser.add_argument('--attn-type', nargs='+', metavar='attn_type', 
                        help='input the attention type for encoders to profile (possile: fourier (alias integral, local), galerkin (alias global), softmax (official PyTorch implementation), linear (standard Q(K^TV) with softmax))',
                        required=True)
    parser.add_argument('--seq-len', type=int, default=8192, metavar='L',
                        help='input sequence length for profiling (default: 8192)')
    parser.add_argument('--dmodel', type=int, default=96, metavar='E',
                        help='input d_model of attention for profiling (default: 96)')
    parser.add_argument('--num-iter', type=int, default=1, metavar='k',
                        help='input number of iteration of backpropagations for profiling (default: 1)')
    parser.add_argument('--reg-layernorm', action='store_true', default=False,
                        help='use the conventional layer normalization')
    parser.add_argument('--no-cuda', action='store_true', default=False,
                        help='disables CUDA in profiling')
    args = parser.parse_args()
    cuda = not args.no_cuda and torch.cuda.is_available()
    device = torch.device('cuda' if cuda else 'cpu')
    current_path = os.path.dirname(os.path.abspath(__file__))
    with open(os.path.join(current_path, r'config.yml')) as f:
        config = yaml.full_load(f)
    config = config['ex1_burgers']
    config['layer_norm'] = args.reg_layernorm
    config['attn_norm'] = not args.reg_layernorm
    config['n_hidden'] = args.dmodel
    attn_types = args.attn_type

    for attn_type in attn_types:
        config['attention_type'] = attn_type
        torch.cuda.empty_cache()
        model = FourierTransformer(**config)
        model = model.to(device)
        print(
            f"\nModel name: {model.__name__}\t Number of params: {get_num_params(model)}")

        node = torch.randn(args.batch_size, args.seq_len, 1).to(device)
        pos = torch.randn(args.batch_size, args.seq_len, 1).to(device)
        target = torch.randn(args.batch_size, args.seq_len, 1).to(device)

        with profiler.profile(profile_memory=True, use_cuda=cuda,) as pf:
            for _ in range(args.num_iter):
                y = model(node, None, pos)
                y = y['preds']
                loss = ((y-target)**2).mean()
                loss.backward()

        sort_by = "self_cuda_memory_usage" if cuda else "self_cpu_memory_usage"
        file_name = os.path.join(HOME, f'ex1_{attn_type}.txt')
        with open(file_name, 'w') as f:
            print(pf.key_averages().table(sort_by=sort_by,
                                        row_limit=300,
                                        header=str(model.__name__) +
                                        ' profiling results',
                                        ), file=f)
        pf_result = ProfileResult(file_name, num_iters=args.num_iter, cuda=cuda)
        pf_result.print_total_mem(['Self CUDA Mem'])
        pf_result.print_total_time()

if __name__ == '__main__':
    main()