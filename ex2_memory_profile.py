from libs import *
import argparse
import torch.autograd.profiler as profiler
DEBUG = False


def main():

    # Training settings
    parser = argparse.ArgumentParser(
        description='Memory profiling of various transformers for Example 2')
    parser.add_argument('--batch-size', type=int, default=4, metavar='N',
                        help='input batch size for profiling (default: 4)')
    parser.add_argument('--subsample-nodes', type=int, default=3, metavar='subsample',
                        help='input fine grid sampling from 421x421 (default: 3 i.e., 141x141 grid)')
    parser.add_argument('--subsample-attn', type=int, default=10, metavar='subsample_attn',
                        help='input coarse grid sampling from 421x421 (default: 10 i.e., 43x43 grid)')
    parser.add_argument('--dmodel', type=int, default=64, metavar='E',
                        help='input d_model of attention for profiling (default: 64)')
    parser.add_argument('--num-iter', type=int, default=1, metavar='k',
                        help='input number of iteration of backpropagations for profiling (default: 1)')
    parser.add_argument('--reg-layernorm', action='store_true', default=False,
                        help='use the conventional layer normalization')
    parser.add_argument('--no-cuda', action='store_true', default=False,
                        help='disables CUDA in profiling')
    args = parser.parse_args()
    cuda = not args.no_cuda and torch.cuda.is_available()
    device = torch.device('cuda' if cuda else 'cpu')

    n_grid = int(((421 - 1)/args.subsample_nodes) + 1)
    n_grid_c = int(((421 - 1)/args.subsample_attn) + 1)
    downsample, upsample = DarcyDataset.get_scaler_sizes(n_grid, n_grid_c)
    downsample = [round(x, 2) for x in downsample]
    current_path = os.path.dirname(os.path.abspath(__file__))
    with open(os.path.join(current_path, r'config.yml')) as f:
        config = yaml.full_load(f)
    config = config['ex2_darcy']
    config['layer_norm'] = args.reg_layernorm
    config['attn_norm'] = not args.reg_layernorm
    config['n_hidden'] = args.dmodel
    config['downscaler_size'] = downsample
    config['upscaler_size'] = upsample

    for attn_type in ['softmax', 'fourier', 'linear', 'galerkin', ]:
        config['attention_type'] = attn_type
        torch.cuda.empty_cache()
        model = FourierTransformer2D(**config)
        model = model.to(device)
        print(
            f"\nModel name: {model.__name__}\t Number of params: {get_num_params(model)}\n")

        node = torch.randn(args.batch_size, n_grid, n_grid, 1).to(device)
        pos = torch.randn(args.batch_size, n_grid_c**2, 2).to(device)
        target = torch.randn(args.batch_size, n_grid, n_grid, 1).to(device)
        grid = torch.randn(args.batch_size, n_grid-2, n_grid-2, 2).to(device)

        with profiler.profile(profile_memory=True, use_cuda=cuda,) as pf:
            for _ in range(args.num_iter):
                y = model(node, None, pos, grid)
                y = y['preds']
                loss = ((y-target)**2).mean()
                loss.backward()

        sort_by = "self_cuda_memory_usage" if cuda else "self_cpu_memory_usage"
        print(pf.key_averages().table(sort_by=sort_by,
                                      row_limit=300,
                                      header=str(model.__name__) +
                                      ' profiling results',
                                      ))


if __name__ == '__main__':
    main()